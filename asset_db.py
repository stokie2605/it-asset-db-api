"""
IT Asset DB API

A small SQLite-backed asset register for tracking hardware inventory by
hostname, MAC address, IP address, and department.
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DATABASE_PATH = Path("it_assets.db")
TABLE_NAME = "HardwareAssets"


@dataclass(frozen=True)
class HardwareAsset:
    AssetID: str
    Hostname: str
    MAC_Address: str
    IP_Address: str
    Department: str


def connect(database_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with row access by column name."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    """Create the hardware asset table if it does not already exist."""
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            AssetID TEXT PRIMARY KEY,
            Hostname TEXT NOT NULL,
            MAC_Address TEXT NOT NULL UNIQUE,
            IP_Address TEXT NOT NULL UNIQUE,
            Department TEXT NOT NULL
        )
        """
    )
    connection.commit()


def validate_asset(asset: HardwareAsset) -> None:
    """Validate required asset fields before writing to SQLite."""
    values = {
        "AssetID": asset.AssetID,
        "Hostname": asset.Hostname,
        "MAC_Address": asset.MAC_Address,
        "IP_Address": asset.IP_Address,
        "Department": asset.Department,
    }

    missing_fields = [field for field, value in values.items() if not value.strip()]
    if missing_fields:
        raise ValueError(f"Missing required asset fields: {', '.join(missing_fields)}")


def insert_asset(connection: sqlite3.Connection, asset: HardwareAsset) -> None:
    """Insert one hardware asset into the asset register."""
    validate_asset(asset)

    try:
        connection.execute(
            f"""
            INSERT INTO {TABLE_NAME}
                (AssetID, Hostname, MAC_Address, IP_Address, Department)
            VALUES
                (:AssetID, :Hostname, :MAC_Address, :IP_Address, :Department)
            """,
            {
                "AssetID": asset.AssetID.strip(),
                "Hostname": asset.Hostname.strip(),
                "MAC_Address": asset.MAC_Address.strip(),
                "IP_Address": asset.IP_Address.strip(),
                "Department": asset.Department.strip(),
            },
        )
        connection.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Asset could not be inserted: {exc}") from exc


def insert_assets(connection: sqlite3.Connection, assets: Iterable[HardwareAsset]) -> None:
    """Insert multiple hardware assets."""
    for asset in assets:
        insert_asset(connection, asset)


def query_assets_by_department(
    connection: sqlite3.Connection,
    department: str,
) -> list[HardwareAsset]:
    """Return all hardware assets assigned to a department."""
    normalized_department = department.strip()
    if not normalized_department:
        raise ValueError("Department query cannot be blank.")

    rows = connection.execute(
        f"""
        SELECT AssetID, Hostname, MAC_Address, IP_Address, Department
        FROM {TABLE_NAME}
        WHERE LOWER(Department) = LOWER(?)
        ORDER BY Hostname ASC
        """,
        (normalized_department,),
    ).fetchall()

    return [
        HardwareAsset(
            AssetID=row["AssetID"],
            Hostname=row["Hostname"],
            MAC_Address=row["MAC_Address"],
            IP_Address=row["IP_Address"],
            Department=row["Department"],
        )
        for row in rows
    ]


def seed_demo_assets(connection: sqlite3.Connection) -> None:
    """Populate the database with deterministic sample assets."""
    demo_assets = [
        HardwareAsset(
            AssetID="AST-1001",
            Hostname="FIN-LAP-001",
            MAC_Address="00:1A:2B:3C:4D:01",
            IP_Address="10.20.10.21",
            Department="Finance",
        ),
        HardwareAsset(
            AssetID="AST-1002",
            Hostname="IT-ADM-WS01",
            MAC_Address="00:1A:2B:3C:4D:02",
            IP_Address="10.20.20.15",
            Department="IT Support",
        ),
        HardwareAsset(
            AssetID="AST-1003",
            Hostname="OPS-WH-TERM01",
            MAC_Address="00:1A:2B:3C:4D:03",
            IP_Address="10.20.30.44",
            Department="Operations",
        ),
        HardwareAsset(
            AssetID="AST-1004",
            Hostname="FIN-DESK-002",
            MAC_Address="00:1A:2B:3C:4D:04",
            IP_Address="10.20.10.22",
            Department="Finance",
        ),
    ]

    for asset in demo_assets:
        try:
            insert_asset(connection, asset)
        except ValueError as exc:
            if "UNIQUE constraint failed" not in str(exc):
                raise


def format_assets(assets: list[HardwareAsset]) -> str:
    """Format asset query results for terminal output."""
    if not assets:
        return "No assets found for that department."

    lines = [
        "AssetID   Hostname        MAC Address        IP Address    Department",
        "--------  --------------  -----------------  ------------  ------------",
    ]

    for asset in assets:
        lines.append(
            f"{asset.AssetID:<8}  "
            f"{asset.Hostname:<14}  "
            f"{asset.MAC_Address:<17}  "
            f"{asset.IP_Address:<12}  "
            f"{asset.Department}"
        )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SQLite-backed IT hardware asset register.",
    )
    parser.add_argument(
        "--department",
        default="Finance",
        help="Department to query after the demo assets are seeded.",
    )
    parser.add_argument(
        "--db",
        default=str(DATABASE_PATH),
        help="SQLite database path. Defaults to it_assets.db.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        database_path = Path(args.db)
        with connect(database_path) as connection:
            initialize_database(connection)
            seed_demo_assets(connection)
            assets = query_assets_by_department(connection, args.department)

        print(f"IT Asset DB API - Department Query: {args.department}")
        print(format_assets(assets))
        print(f"\nDatabase file: {database_path.resolve()}")
        return 0
    except (ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
