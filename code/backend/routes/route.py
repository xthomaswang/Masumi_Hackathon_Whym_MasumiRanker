#backend/routes/route.py

"""
backend/routes/route.py
All API endpoints for MasumiRanker.

Mounted under "/api" in main.py
"""

from datetime import datetime, timezone
import hashlib
from typing import List, Dict, Any, Generator, Optional

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.database.models import Agent, Rating, RegistryEntry, Recommendation
from backend.database.recommend_db import SessionRecommend


router = APIRouter(tags=["ranker"])

# ───────────────────────────── helpers ─────────────────────────────────────────
def paginate(items: list, page: int = 1, size: int = 20) -> Dict[str, Any]:
    start, end = (page - 1) * size, (page * size)
    return {
        "items": items[start:end],
        "page": page,
        "page_size": size,
        "total_items": len(items),
    }


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def agent_id_from_did(db: Session, did: str) -> str | None:
    agent = db.query(Agent).filter_by(did=did).first()
    return agent.id if agent else None


def utc_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()

# ───────────────────────────── schemas ────────────────────────────────────────
class AgentOut(BaseModel):
    id: str
    name: str
    category: str
    description: str
    did: str
    url: str
    img_url: str | None = None     
    price_usd: float
    avg_score: float
    num_ratings: int

    model_config = ConfigDict(from_attributes=True)


class RatingIn(BaseModel):
    agent_id: str
    user_id: Optional[str] = None 
    score: int = Field(..., ge=1, le=5)
    comment: str = Field("", max_length=1_000)


class RatingOut(RatingIn):
    timestamp: str
    hash: str
    did: Optional[str] = None # filled when querying


class PaginatedAgents(BaseModel):
    items: List[AgentOut]
    page: int
    page_size: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class PaginatedRatings(BaseModel):
    items: List[RatingOut]
    page: int
    page_size: int
    total_items: int


class RegistryListSchema(BaseModel):
    data: Dict[str, List[Dict[str, Any]]]
    status: str


class RegistryEntrySchema(BaseModel):
    data: Dict[str, Any]
    status: str

# ─────────────────────────── ranker endpoints ────────────────────────────────
@router.get("/agents", response_model=PaginatedAgents)
def get_agents(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """Paginated list of agents ordered by average score."""
    query = db.query(Agent).order_by(Agent.avg_score.desc())
    return paginate(query.all(), page, page_size)


@router.post("/ratings", response_model=RatingOut, status_code=201)
def submit_rating(p: RatingIn, db: Session = Depends(get_db)):
    """Submit a rating + comment for an agent."""
    agent = db.get(Agent, p.agent_id)
    if not agent:
        raise HTTPException(status_code=400, detail="Invalid agent_id")

    timestamp = utc_iso()
    rating_hash = hashlib.sha256(f"{p.agent_id}{timestamp}".encode()).hexdigest()

    db.add(Rating(**p.dict(), timestamp=timestamp, hash=rating_hash))
    agent.avg_score = round(
        (agent.avg_score * agent.num_ratings + p.score) / (agent.num_ratings + 1), 2
    )
    agent.num_ratings += 1
    db.commit()

    return RatingOut(**p.dict(), timestamp=timestamp, hash=rating_hash)


# ───────────── Ratings lookup (DID & AgentID via Query) ─────────────
@router.get("/ratings/by-did", response_model=PaginatedRatings)
def get_ratings_by_did(
    did: str = Query(..., description="Agent DID"),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    agent_id = agent_id_from_did(db, did)
    if not agent_id:
        raise HTTPException(status_code=404, detail="DID not found")

    rows = db.query(Rating).filter_by(agent_id=agent_id).all()
    items = [
        RatingOut.model_validate(r, from_attributes=True).model_copy(update={"did": did})
        for r in rows
    ]
    return paginate(items, page, page_size)


@router.get("/ratings/by-agent", response_model=PaginatedRatings)
def get_ratings_by_agent(
    agent_id: str = Query(..., description="Agent ID"),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    rows = db.query(Rating).filter_by(agent_id=agent_id).all()
    if not rows:
        # could be "no ratings" or "agent not found" – decide your UX
        if not db.get(Agent, agent_id):
            raise HTTPException(status_code=404, detail="Agent not found")
    items = [RatingOut.model_validate(r, from_attributes=True) for r in rows]
    return paginate(items, page, page_size)


# Deprecated path parameter version
@router.get("/ratings/{_agent_id}", include_in_schema=False)
def _deprecated_ratings(*_):
    raise HTTPException(status_code=410, detail="Use /ratings/by-agent?agent_id= or /ratings/by-did?did=")

# ─────────────────────── Masumi mock API ──────────────────────────────────────
@router.post("/registry-entry/", response_model=RegistryListSchema)
def registry_entry(
    limit: int = Body(10, embed=True, ge=1, le=50),
    db: Session = Depends(get_db),
):
    rows = db.query(RegistryEntry).limit(limit).all()
    return {"data": {"entries": [r.full_json for r in rows]}, "status": "success"}


@router.get("/payment-information/", response_model=RegistryEntrySchema)
def payment_info(
    agentIdentifier: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
):
    row = db.query(RegistryEntry).filter(RegistryEntry.id == agentIdentifier).first()
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"data": row.full_json, "status": "success"}


@router.post("/recommendations", status_code=201)
def add_recommendation(
    did: str = Body(..., embed=True, min_length=3),
    db: Session = Depends(get_db),
):
    if not agent_id_from_did(db, did):
        raise HTTPException(status_code=404, detail="DID not found")

    rec_session = SessionRecommend()
    try:
        rec = Recommendation(did=did)          
        rec_session.add(rec)
        rec_session.commit()
        rec_session.refresh(rec)
    finally:
        rec_session.close()

    return {"status": "success", "did": did, "timestamp": rec.timestamp.isoformat()}