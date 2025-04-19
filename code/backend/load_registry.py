#/backend/load_registry.py

"""
backend/load_registry.py
────────────────────────
Populate the local database with mock Masumi data.

• masumi_entries.json  – 50 agents in official registry format
• masumi_comments.json – 500 ratings (10 per agent)

Place both files in  <project_root>/dataset/
"""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import uuid  # kept for future use (not strictly needed here)

from backend.database.database import SessionLocal, engine, Base
from backend.database.models import Agent, Rating, RegistryEntry

# ───────────────────────────── paths ──────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR  = PROJECT_ROOT / "dataset"
ENTRIES_JSON = DATASET_DIR / "masumi_entries.json"
COMMENTS_JSON = DATASET_DIR / "masumi_comments.json"

# ────────────────────────── helpers ───────────────────────────────
def category_from_name(name: str) -> str:
    """FinanceAdvisor-1 → FinanceAdvisor"""
    return name.split("-", 1)[0] if "-" in name else "Unknown"


def utc_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def sha256_hex(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


def extract_usd_price(entry_json: dict) -> float:
    """
    Convert AgentPricing → float USD per query/request/session.
    Assumes the 'unit' field contains 'USD'.  Tokens like USDC, USDM
    can be mapped 1:1 or converted here if needed.
    """
    try:
        amounts = entry_json["AgentPricing"]["FixedPricing"]["Amounts"]
        for amt in amounts:
            if "USD" in amt["unit"]:
                return float(amt["amount"])
    except Exception:
        pass
    return 0.0

# ────────────────────────── main loader ───────────────────────────
def main() -> None:
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # Load mock JSON files
    entries   = json.load(open(ENTRIES_JSON,  encoding="utf-8"))["data"]["entries"]
    comments  = json.load(open(COMMENTS_JSON, encoding="utf-8"))["data"]["comments"]

    # Build DID → agent_id map for comment import
    did_to_agent_id = {e["did"]: e["id"] for e in entries}

    with SessionLocal() as db:
        # ─── upsert agents + registry blobs ────────────────────────
        for entry in entries:
            price_usd = extract_usd_price(entry)

            agent = db.get(Agent, entry["id"])
            if agent:
                # update existing record
                agent.name        = entry["name"]
                agent.category    = category_from_name(entry["name"])
                agent.description = entry["description"]
                agent.did         = entry["did"]
                agent.url         = entry["apiBaseUrl"]
                agent.price_usd   = price_usd
                agent.img_url     = entry["image"]
            else:
                # insert new record
                db.add(
                    Agent(
                        id          = entry["id"],
                        name        = entry["name"],
                        category    = category_from_name(entry["name"]),
                        description = entry["description"],
                        did         = entry["did"],
                        url         = entry["apiBaseUrl"],
                        price_usd   = price_usd,
                        img_url     = entry["image"]
                    )
                )

            # upsert full JSON blob
            reg = db.get(RegistryEntry, entry["id"])
            if reg:
                reg.full_json = entry
            else:
                db.add(RegistryEntry(id=entry["id"], full_json=entry))

        # ─── insert ratings ────────────────────────────────────────
        for c in comments:
            agent_id = did_to_agent_id.get(c["id"])
            if not agent_id:
                continue  # orphan DID – skip

            db.add(
                Rating(
                    agent_id  = agent_id,
                    user_id   = None,
                    score     = int(c["rating"]),
                    comment   = c["comment"],
                    timestamp = utc_iso(),
                    hash      = sha256_hex(c["comment"] + str(c["rating"])),
                )
            )

        db.commit()

        # ─── recompute aggregate scores ────────────────────────────
        for agent in db.query(Agent).all():
            rows = db.query(Rating).filter(Rating.agent_id == agent.id).all()
            if rows:
                agent.num_ratings = len(rows)
                agent.avg_score   = sum(r.score for r in rows) / len(rows)
        db.commit()

        print(f"Imported {len(entries)} agents and {len(comments)} ratings.")


if __name__ == "__main__":
    main()
