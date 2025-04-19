# backend/main.py
"""
FastAPI backend with:
- Ranker endpoints (/agents, /ratings …)
- Masumi‑compatible mock endpoints:
    POST /registry-entry/      -> list entries
    GET  /payment-information/ -> single entry
"""
from fastapi import FastAPI, HTTPException, Depends, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
from sqlalchemy.orm import Session
import uvicorn

from backend.database.database import SessionLocal, Base, engine
from backend.database.models import Agent, Rating, RegistryEntry

# ----------------------------------------------------------------
app = FastAPI(title="Masumi Ranker API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

# ----------------------------------------------------------------
class AgentOut(BaseModel):
    id: str; name: str; category: str; description: str; did: str; url: str
    avg_score: float; num_ratings: int
    model_config = ConfigDict(from_attributes=True)

class RatingIn(BaseModel):
    agent_id: str; user_id: str
    score: int = Field(..., ge=1, le=5)
    comment: str = Field("", max_length=1000)

class RatingOut(RatingIn):
    timestamp: str; hash: str

class PaginatedAgents(BaseModel):
    items: List[AgentOut]; page: int; page_size: int; total_items: int
    model_config = ConfigDict(from_attributes=True)

class PaginatedRatings(BaseModel):
    items: List[RatingOut]; page: int; page_size: int; total_items: int

class RegistryListSchema(BaseModel):
    data: Dict[str, List[Dict[str, Any]]]; status: str

class RegistryEntrySchema(BaseModel):
    data: Dict[str, Any]; status: str

# ----------------------------------------------------------------
def paginate(arr, page=1, size=20):
    start = (page-1)*size; end = start+size
    return dict(items=arr[start:end], page=page, page_size=size, total_items=len(arr))

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# ----------------- Ranker endpoints --------------------------------
@app.get("/agents", response_model=PaginatedAgents)
def get_agents(page:int=1, page_size:int=20, db:Session=Depends(get_db)):
    q = db.query(Agent).order_by(Agent.avg_score.desc())
    return paginate(q.all(), page, page_size)

@app.post("/ratings", response_model=RatingOut, status_code=201)
def submit_rating(p:RatingIn, db:Session=Depends(get_db)):
    ag = db.get(Agent, p.agent_id)
    if not ag: raise HTTPException(400, "Invalid agent_id")
    ts = datetime.utcnow().isoformat()
    h = hashlib.sha256(f"{p.agent_id}{ts}".encode()).hexdigest()
    db.add(Rating(**p.dict(), timestamp=ts, hash=h))
    ag.avg_score = round((ag.avg_score*ag.num_ratings+p.score)/(ag.num_ratings+1),2)
    ag.num_ratings += 1
    db.commit()
    return RatingOut(**p.dict(), timestamp=ts, hash=h)

@app.get("/ratings/{agent_id}", response_model=PaginatedRatings)
def get_ratings(agent_id:str, page:int=1, page_size:int=20, db:Session=Depends(get_db)):
    rs = db.query(Rating).filter_by(agent_id=agent_id).all()
    items = [RatingOut.model_validate(r, from_attributes=True) for r in rs]
    return paginate(items, page, page_size)

# ----------------- Masumi mock endpoints ---------------------------
@app.post("/registry-entry/", response_model=RegistryListSchema)
def registry_entry(limit:int=Body(10, embed=True, ge=1, le=50),
                   db:Session=Depends(get_db)):
    rows = db.query(RegistryEntry).limit(limit).all()
    return {"data":{"entries":[r.full_json for r in rows]}, "status":"success"}

@app.get("/payment-information/", response_model=RegistryEntrySchema)
def payment_info(agentIdentifier:str=Query(..., min_length=3),
                 db:Session=Depends(get_db)):
    row = db.query(RegistryEntry).filter(RegistryEntry.id==agentIdentifier).first()
    if not row:
        raise HTTPException(404, "Entry not found")
    return {"data":row.full_json, "status":"success"}

# -------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
