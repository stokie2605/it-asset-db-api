import sqlite3
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import asset_db


from fastapi.middleware.cors import CORSMiddleware

# Pydantic model for incoming requests
class Asset(BaseModel):
    AssetID: str
    Hostname: str
    MAC_Address: str
    IP_Address: str
    Department: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database and seed demo assets on startup
    with asset_db.connect() as connection:
        asset_db.initialize_database(connection)
        asset_db.seed_demo_assets(connection)
    yield
    # No teardown needed for SQLite


app = FastAPI(
    title="IT Asset DB API",
    description="A REST API for tracking hardware inventory.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow React frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For demo purposes, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Check if the API is running and database is accessible."""
    try:
        with asset_db.connect() as connection:
            connection.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


@app.get("/assets", response_model=List[Asset])
def get_assets(department: Optional[str] = None):
    """Get assets, optionally filtered by department."""
    with asset_db.connect() as connection:
        if department:
            try:
                db_assets = asset_db.query_assets_by_department(connection, department)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            # The existing code doesn't have a get_all, so we'll just write a quick query here
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                f"SELECT AssetID, Hostname, MAC_Address, IP_Address, Department FROM {asset_db.TABLE_NAME} ORDER BY Hostname ASC"
            ).fetchall()
            db_assets = [
                asset_db.HardwareAsset(
                    AssetID=row["AssetID"],
                    Hostname=row["Hostname"],
                    MAC_Address=row["MAC_Address"],
                    IP_Address=row["IP_Address"],
                    Department=row["Department"],
                )
                for row in rows
            ]
            
        return [
            Asset(
                AssetID=a.AssetID,
                Hostname=a.Hostname,
                MAC_Address=a.MAC_Address,
                IP_Address=a.IP_Address,
                Department=a.Department,
            )
            for a in db_assets
        ]


@app.post("/assets", status_code=201)
def create_asset(asset: Asset):
    """Add a new hardware asset to the register."""
    new_asset = asset_db.HardwareAsset(
        AssetID=asset.AssetID,
        Hostname=asset.Hostname,
        MAC_Address=asset.MAC_Address,
        IP_Address=asset.IP_Address,
        Department=asset.Department,
    )
    
    with asset_db.connect() as connection:
        try:
            asset_db.insert_asset(connection, new_asset)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    return {"message": "Asset created successfully", "asset_id": asset.AssetID}
