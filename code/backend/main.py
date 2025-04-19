# backend/main.py

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import hashlib
from typing import List, Optional
from sqlalchemy.orm import Session
import uvicorn

from backend.database.database import engine, SessionLocal, Base
from backend.database.models import Agent, Rating

app = FastAPI(title="Masumi Ranker API")

# ----- CORS -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Create tables -----
Base.metadata.create_all(bind=engine)

# ----- Pydantic Schemas -----
class AgentOut(BaseModel):
    id: str
    name: str
    category: str
    description: str
    did: str
    url: str
    avg_score: float
    num_ratings: int

    model_config = ConfigDict(from_attributes=True)

class RatingIn(BaseModel):
    agent_id: str
    user_id: str
    score: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(default="", max_length=1000)

class RatingOut(RatingIn):
    timestamp: str
    hash: str

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

# ----- Simulated registry data -----
registry_db = [
    {
        "did": "did:masumi:abc123",
        "name": "Coding Mentor",
        "description": "Helps you learn to code.",
        "owner": "TeamA",
        "url": "https://example.com/codingmentor",
        "category": "Education",
    },
    {
        "did": "did:masumi:def456",
        "name": "SEO Optimizer",
        "description": "Optimizes your SEO.",
        "owner": "TeamB",
        "url": "https://example.com/seo",
        "category": "Marketing",
    },
]

# ----- Helper functions -----
def paginate(items, page: int = 1, page_size: int = 20):
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total_items": total,
    }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----- Routes -----
@app.get("/agents", response_model=PaginatedAgents)
def get_agents(
    category: Optional[str] = None,
    sort_by: str = "avg_score",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """
    Return a paginated list of agents, filterable by category and sortable by `avg_score` or `num_ratings`.
    """
    query = db.query(Agent)
    if category:
        query = query.filter(Agent.category == category)
    if sort_by == "num_ratings":
        query = query.order_by(Agent.num_ratings.desc())
    else:
        query = query.order_by(Agent.avg_score.desc())
    agents = query.all()
    return paginate(agents, page, page_size)

@app.get("/agents/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """
    Return a single agent by ID.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@app.get("/registry-api/agents")
def get_registry(
    category: Optional[str] = None,
    owner: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    Return simulated registry entries. Supports filtering by `category` or `owner`.
    """
    result = registry_db
    if category:
        result = [r for r in result if r["category"] == category]
    if owner:
        result = [r for r in result if r["owner"] == owner]
    return paginate(result, page, page_size)

@app.post("/ratings", response_model=RatingOut, status_code=201)
def submit_rating(payload: RatingIn, db: Session = Depends(get_db)):
    """
    Submit a new rating and update the agent's aggregate statistics.
    """
    agent = db.query(Agent).filter(Agent.id == payload.agent_id).first()
    if not agent:
        raise HTTPException(status_code=400, detail="Invalid agent_id")

    timestamp = datetime.utcnow().isoformat()
    data = f"{payload.agent_id}{payload.user_id}{payload.score}{payload.comment}{timestamp}"
    hash_val = hashlib.sha256(data.encode()).hexdigest()

    rating = Rating(
        agent_id=payload.agent_id,
        user_id=payload.user_id,
        score=payload.score,
        comment=payload.comment,
        timestamp=timestamp,
        hash=hash_val,
    )
    db.add(rating)

    # Update aggregate stats
    total_score = agent.avg_score * agent.num_ratings + payload.score
    agent.num_ratings += 1
    agent.avg_score = round(total_score / agent.num_ratings, 2)

    db.commit()
    return RatingOut(**payload.dict(), timestamp=timestamp, hash=hash_val)

@app.get("/ratings/{agent_id}", response_model=PaginatedRatings)
def get_agent_ratings(
    agent_id: str,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """
    Return paginated ratings for a given agent.
    """
    ratings = (
        db.query(Rating)
        .filter(Rating.agent_id == agent_id)
        .order_by(Rating.timestamp.desc())
        .all()
    )
    # Convert ORM list to Pydantic list
    items = [RatingOut.model_validate(r, from_attributes=True) for r in ratings]
    return paginate(items, page, page_size)

@app.get("/rankings", response_model=List[AgentOut])
def get_rankings(
    category: Optional[str] = None,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """
    Return top agents ranked by average score.
    """
    query = db.query(Agent)
    if category:
        query = query.filter(Agent.category == category)
    agents = query.order_by(Agent.avg_score.desc()).limit(limit).all()
    return agents

@app.post("/sync-registry")
def sync_registry(db: Session = Depends(get_db)):
    """
    Synchronize simulated registry entries into the agents table.
    """
    for entry in registry_db:
        exists = db.query(Agent).filter(Agent.id == entry["did"]).first()
        if not exists:
            db.add(
                Agent(
                    id=entry["did"],
                    name=entry["name"],
                    category=entry["category"],
                    description=entry["description"],
                    did=entry["did"],
                    url=entry["url"],
                )
            )
    db.commit()
    return {"message": "Registry data synced to agents table."}

# ----- Entry point -----
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
