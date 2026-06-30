import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Create a temporary database file for the test session
TEST_DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DB_PATH = Path(TEST_DB_FILE.name)
TEST_DB_FILE.close()

# Monkeypatch the connect function in the library to force using the test DB
import asset_db
original_connect = asset_db.connect

def mock_connect(database_path=None):
    if database_path is None:
        database_path = TEST_DB_PATH
    return original_connect(database_path)

asset_db.connect = mock_connect

# Now import the FastAPI app and TestClient
from main import app

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Ensure database schema is initialized and seeded once before tests."""
    with asset_db.connect(TEST_DB_PATH) as conn:
        asset_db.initialize_database(conn)
        asset_db.seed_demo_assets(conn)
    yield
    # Clean up test database file
    try:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    except PermissionError:
        pass


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_get_assets_all():
    response = client.get("/assets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # The database was seeded with 4 assets on startup
    assert len(data) >= 4
    # Check that they have the required fields
    for asset in data:
        assert "AssetID" in asset
        assert "Hostname" in asset
        assert "MAC_Address" in asset
        assert "IP_Address" in asset
        assert "Department" in asset


def test_get_assets_filter_by_department():
    response = client.get("/assets?department=Finance")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for asset in data:
        assert asset["Department"] == "Finance"


def test_get_assets_filter_by_department_case_insensitive():
    response = client.get("/assets?department=fInAnCe")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_assets_filter_blank():
    response = client.get("/assets?department=%20%20")
    # A blank department filter should return 400 Bad Request
    assert response.status_code == 400
    assert "Department query cannot be blank" in response.json()["detail"]


def test_create_asset_success():
    new_asset = {
        "AssetID": "AST-2001",
        "Hostname": "HR-LAP-009",
        "MAC_Address": "00:1A:2B:3C:4D:99",
        "IP_Address": "10.20.90.11",
        "Department": "Human Resources"
    }
    response = client.post("/assets", json=new_asset)
    assert response.status_code == 201, f"Response: {response.json()}"
    assert response.json() == {"message": "Asset created successfully", "asset_id": "AST-2001"}

    # Verify we can retrieve it
    get_resp = client.get("/assets?department=Human Resources")
    assert get_resp.status_code == 200
    assert len(get_resp.json()) == 1
    assert get_resp.json()[0]["Hostname"] == "HR-LAP-009"


def test_create_asset_duplicate_mac():
    # IP is unique, MAC is duplicate of seeded AST-1001 ("00:1A:2B:3C:4D:01")
    dup_asset = {
        "AssetID": "AST-2002",
        "Hostname": "HR-LAP-010",
        "MAC_Address": "00:1A:2B:3C:4D:01",
        "IP_Address": "10.20.90.12",
        "Department": "Human Resources"
    }
    response = client.post("/assets", json=dup_asset)
    assert response.status_code == 400
    assert "UNIQUE constraint failed: HardwareAssets.MAC_Address" in response.json()["detail"]


def test_create_asset_missing_fields_validation():
    # Empty host name
    bad_asset = {
        "AssetID": "AST-2003",
        "Hostname": "   ",
        "MAC_Address": "00:1A:2B:3C:4D:98",
        "IP_Address": "10.20.90.13",
        "Department": "Human Resources"
    }
    response = client.post("/assets", json=bad_asset)
    assert response.status_code == 400
    assert "Missing required asset fields: Hostname" in response.json()["detail"]
