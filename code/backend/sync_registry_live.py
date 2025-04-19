#/backend/sync_registry_live.py
"""
Fetch live Registry entries from Masumi official API and upsert into SQLite.

Run once:
    python -m backend.sync_registry_live

To schedule:
    import backend.sync_registry_live as s; s.run_sync()
"""

import os, json, uuid, logging
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

from backend.database.database import SessionLocal, engine, Base
from backend.database.models import RegistryEntry

# ------------------------------------------------------------------#
# Config
# ------------------------------------------------------------------#
ROOT = Path(__file__).resolve().parents[1]        # project root
load_dotenv(dotenv_path=ROOT / ".env")

REGISTRY_URL = os.getenv("MASUMI_REGISTRY_URL")
API_TOKEN     = os.getenv("MASUMI_API_TOKEN")
NETWORK       = os.getenv("MASUMI_NETWORK", "Preprod")
SYNC_LIMIT    = int(os.getenv("SYNC_LIMIT", 50))

HEADERS = {
    "Content-Type": "application/json",
    "token": API_TOKEN
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")

# ------------------------------------------------------------------#
def fetch_entries(limit: int) -> list[dict]:
    """Call official Masumi endpoint and return entries array."""
    payload = { "network": NETWORK, "limit": limit }
    res = requests.post(REGISTRY_URL, headers=HEADERS, json=payload, timeout=20)
    res.raise_for_status()
    return res.json()["data"]["entries"]

def upsert_entries(entries: list[dict]) -> None:
    """Insert new or update existing rows."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        inserted = updated = 0
        for e in entries:
            row = db.get(RegistryEntry, e["agentIdentifier"])
            if row:
                row.full_json = e
                updated += 1
            else:
                db.add(RegistryEntry(id=e["agentIdentifier"], full_json=e))
                inserted += 1
        db.commit()
    logging.info(f"Inserted {inserted}, updated {updated} registry entries")

def run_sync() -> None:
    logging.info("Syncing registry from Masumi …")
    try:
        entries = fetch_entries(SYNC_LIMIT)
        upsert_entries(entries)
        logging.info("Sync complete")
    except Exception as exc:
        logging.error(f"Sync failed: {exc}")

# ------------------------------------------------------------------#
if __name__ == "__main__":
    run_sync()
