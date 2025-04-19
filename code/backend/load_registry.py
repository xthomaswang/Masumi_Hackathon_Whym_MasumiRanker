# backend/load_registry.py
import json, uuid
from pathlib import Path
from backend.database.database import SessionLocal, engine, Base
from backend.database.models import RegistryEntry

PROJECT_ROOT = Path(__file__).resolve().parents[2]  #  .. / ..
DATASET = PROJECT_ROOT / "dataset" / "agents_mock.json"

def build_full_json(raw: dict) -> dict:
    """Convert one agents_mock item to official Masumi registry JSON."""
    cuid = str(uuid.uuid4())              # fake NFT id
    return {
        "name": raw["name"],
        "description": raw["description"],
        "status": "Online",
        "RegistrySource": {
            "type": "Web3CardanoV1",
            "policyId": "0000000000000000000000000000000000000000000000000000000000000000",
            "url": None
        },
        "Capability": {
            "name": raw["capability"]["name"],
            "version": raw["capability"]["version"]
        },
        "PaymentIdentifier": [],          # omitted in mock
        "AgentPricing": {
            "pricingType": "Fixed",
            "FixedPricing": { "Amounts": raw["pricing"] }
        },
        "authorContactEmail": raw["author"]["contact"],
        "authorContactOther": None,
        "authorName": raw["author"]["name"],
        "apiBaseUrl": raw["api_url"],
        "ExampleOutput": [{
            "name": "Example Output",
            "mimeType": "text/plain",
            "url": raw["example_output"]
        }],
        "image": raw["image"],
        "otherLegal": None,
        "privacyPolicy": raw["legal"]["privacy_policy"],
        "tags": raw["tags"],
        "termsAndCondition": raw["legal"]["terms"],
        "uptimeCheckCount": 0,
        "uptimeCount": 0,
        "lastUptimeCheck": "1970-01-01T00:00:00.000Z",
        "authorOrganization": raw["author"]["organization"],
        "agentIdentifier": raw["name"],   # use name as identifier
        "id": cuid
    }

def main():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        items = json.load(open(DATASET, "r", encoding="utf-8"))["agents"]
        for it in items:
            rid = it["name"]              # primary key
            if db.get(RegistryEntry, rid):
                continue
            db.add(RegistryEntry(id=rid, full_json=build_full_json(it)))
        db.commit()
        print(f"Inserted {len(items)} registry rows")

if __name__ == "__main__":
    main()
