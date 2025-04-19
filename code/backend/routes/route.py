# backend/routes/route.py – API endpoints for MasumiRanker (mounted under /api prefix in main.py)

import logging
import json
import numpy as np
import faiss
from pathlib import Path
from datetime import datetime, timezone
import hashlib
from typing import List, Dict, Any, Generator, Optional

from fastapi import APIRouter, HTTPException, Depends, Body, Query, Request
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import distinct # For querying distinct DIDs

# --- Database and Model Imports ---
from backend.database.database import SessionLocal # Main DB Session factory
# Import all models (Agent, Rating etc. use main Base; Recommendation, RecommendedAgent use RecommendBase)
from backend.database.models import Agent, Rating, RegistryEntry, Recommendation, RecommendedAgent
try:
    # Import the separate Session factory for recommend.db
    from backend.database.recommend_db import SessionRecommend
except ImportError:
    SessionRecommend = None
    logging.warning("Recommendation DB session factory (SessionRecommend) not found or import failed.")

# --- Router Setup ---
# Prefix "/api" should be applied in main.py when including this router
router = APIRouter(tags=["MasumiRanker API"])

# --------------------- Helper Functions ---------------------
def paginate(items: list, page: int = 1, size: int = 20) -> Dict[str, Any]:
    """Helper function to paginate a list of items."""
    if page < 1: page = 1
    if size < 1: size = 1
    start = (page - 1) * size
    end = page * size
    total_items = len(items)
    paginated_items = items[start:end]
    logging.debug(f"Paginating: page={page}, size={size}, total_items={total_items}, returning {len(paginated_items)} items.")
    return {"items": paginated_items, "page": page, "page_size": size, "total_items": total_items}

def get_db() -> Generator[Session, None, None]:
    """Dependency function to get a main database (e.g., masumi.db) session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_recommend_db() -> Optional[Generator[Session, None, None]]:
    """Dependency function to get a recommendation database (recommend.db) session."""
    if SessionRecommend:
        db = SessionRecommend()
        try:
            yield db
        finally:
            db.close()
    else:
        # Yield None if the recommendation DB session factory isn't available
        yield None

def agent_id_from_did(db: Session, did: str) -> Optional[str]:
    """Retrieve agent's internal ID from its DID using the main database."""
    try:
        agent = db.query(Agent).filter(Agent.did == did).first()
        return agent.id if agent else None
    except SQLAlchemyError as e:
        logging.error(f"Database error finding agent by DID {did}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error retrieving agent.")

def utc_iso() -> str:
    """Get the current time in UTC ISO 8601 format string."""
    return datetime.now(tz=timezone.utc).isoformat()

# --------------------- Pydantic Schemas ---------------------
# Schemas for data validation and API response structure

class AgentOut(BaseModel):
    """Schema for returning agent details to the client."""
    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = ""
    did: str
    url: Optional[str] = None
    price_usd: Optional[float] = 0.0 # Use Optional if they can be null in DB/logic
    avg_score: Optional[float] = 0.0
    num_ratings: Optional[int] = 0
    img_url: Optional[str] = None # Populated dynamically

    model_config = ConfigDict(from_attributes=True) # Enable ORM mode

class RatingIn(BaseModel):
    """Schema for submitting a new rating."""
    agent_id: str # Internal ID of the agent being rated
    user_id: Optional[str] = None # Optional identifier for the user submitting the rating
    score: int = Field(..., ge=1, le=5, description="Rating score (1-5)")
    comment: str = Field("", max_length=1000, description="Optional user comment")

class RatingOut(RatingIn):
    """Schema for returning rating details, including server-generated fields."""
    timestamp: str # ISO 8601 timestamp
    hash: str # Hash of the rating details
    did: Optional[str] = None # Agent DID, potentially added for context

    model_config = ConfigDict(from_attributes=True)

class PaginatedAgents(BaseModel):
    """Schema for paginated list of agents."""
    items: List[AgentOut]
    page: int
    page_size: int
    total_items: int

class PaginatedRatings(BaseModel):
    """Schema for paginated list of ratings."""
    items: List[RatingOut]
    page: int
    page_size: int
    total_items: int

class RegistryListSchema(BaseModel):
    """Schema for list of raw registry entries (if sync were enabled)."""
    data: Dict[str, List[Dict[str, Any]]] # Structure depends on Masumi API
    status: str

class RegistryEntrySchema(BaseModel):
    """Schema for a single raw registry entry (if sync were enabled)."""
    data: Dict[str, Any] # Structure depends on Masumi API
    status: str

class RecommendationStatus(BaseModel):
    """Schema for response after POSTing a recommendation event."""
    status: str
    did: str
    timestamp: str # ISO 8601 timestamp

class QueryRequest(BaseModel):
    """Schema for semantic search request."""
    query: str = Field(..., description="Natural language query string.")
    top_k: int = Field(3, ge=1, le=50, description="Number of top similar agents to return.")

class AgentResult(BaseModel):
    """Schema for representing a single agent in search results."""
    id: str # agentIdentifier or internal id from the indexed agents.json
    did: str
    name: str
    description: Optional[str] = ""
    score: float # Similarity score from Faiss search

class QueryResponse(BaseModel):
    """Schema for the semantic search response."""
    results: List[AgentResult]

class RecommendationListResponse(BaseModel):
    """Schema for returning the list of distinct recommended DIDs."""
    dids: List[str]

# --------------------- Image URL Helper ---------------------

def _attach_img(agent_obj: Agent) -> AgentOut:
    """
    Helper to create AgentOut schema from an Agent DB object
    and construct the correct image URL path.
    """
    try:
        # Create Pydantic model from ORM object
        out = AgentOut.model_validate(agent_obj)
        # Check if the agent has an associated image filename/path in the database
        if agent_obj.img_url:
            # Extract just the filename part
            filename = Path(agent_obj.img_url).name
            # Construct the URL path relative to the server root, matching StaticFiles mount point
            out.img_url = f"/images/{filename}"
        else:
            # Ensure img_url is None in the output if not set in DB
            out.img_url = None
        return out
    except Exception as e:
        # Log error and raise HTTPException for the endpoint handler to catch
        logging.error(f"Error processing agent image data (ID: {getattr(agent_obj, 'id', 'N/A')}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing agent image data.")

# --------------------- API Endpoints ---------------------

# --- Agent Endpoints (using main DB: masumi.db) ---
@router.get("/agents", response_model=PaginatedAgents, tags=["Agents"])
def get_agents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of agents per page"),
    db: Session = Depends(get_db) # Depends on main DB session
):
    """Retrieve a paginated list of agents from the main database, ordered by score."""
    logging.info(f"Request received for GET /agents: page={page}, page_size={page_size}")
    try:
        db_agents = db.query(Agent).order_by(Agent.avg_score.desc()).all()
        # Use helper to process image URLs for each agent
        items = [_attach_img(a) for a in db_agents]
        response = paginate(items, page=page, size=page_size)
        logging.info(f"Returning {len(response['items'])} agents for page {page}.")
        return response
    except HTTPException: raise # Re-raise exceptions from helpers
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error fetching agents.")
    except Exception as e:
        logging.error(f"Unexpected error fetching agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching agents.")

@router.get("/agents/{agent_id}", response_model=AgentOut, tags=["Agents"])
def read_agent(agent_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific agent by its internal ID from the main database."""
    logging.info(f"Request received for GET /agents/{agent_id}")
    try:
        db_agent = db.get(Agent, agent_id) # Use db.get for primary key lookup
        if not db_agent:
            logging.warning(f"Agent not found for ID: {agent_id}")
            raise HTTPException(status_code=404, detail="Agent not found")
        response = _attach_img(db_agent) # Process image URL
        logging.info(f"Returning details for agent ID: {agent_id}")
        return response
    except HTTPException: raise
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error fetching agent.")
    except Exception as e:
        logging.error(f"Unexpected error fetching agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching agent.")

# --- Rating Endpoints (using main DB: masumi.db) ---
@router.post("/ratings", response_model=RatingOut, status_code=201, tags=["Ratings"])
def submit_rating(p: RatingIn, db: Session = Depends(get_db)):
    """Submit a rating and comment for an agent, stored in the main database."""
    logging.info(f"Request received for POST /ratings for agent_id: {p.agent_id}")
    try:
        agent = db.get(Agent, p.agent_id)
        if not agent:
            logging.warning(f"Attempted to rate non-existent agent ID: {p.agent_id}")
            raise HTTPException(status_code=400, detail="Invalid agent_id provided.")

        timestamp = utc_iso()
        rating_hash_content = f"{p.agent_id}{p.user_id or ''}{timestamp}{p.score}{p.comment}"
        rating_hash = hashlib.sha256(rating_hash_content.encode()).hexdigest()

        new_rating = Rating(**p.model_dump(), timestamp=timestamp, hash=rating_hash)
        db.add(new_rating)

        # Safely update agent's average score and rating count
        current_total_score = (agent.avg_score or 0.0) * (agent.num_ratings or 0)
        new_num_ratings = (agent.num_ratings or 0) + 1
        agent.avg_score = round((current_total_score + p.score) / new_num_ratings, 2)
        agent.num_ratings = new_num_ratings
        logging.debug(f"Updating agent {p.agent_id}: score={agent.avg_score}, num_ratings={agent.num_ratings}")

        db.commit()
        db.refresh(new_rating)
        logging.info(f"Rating submitted successfully for agent ID: {p.agent_id}")
        return RatingOut.model_validate(new_rating)

    except HTTPException: raise
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"Database error submitting rating for agent {p.agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error submitting rating.")
    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected error submitting rating for agent {p.agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error submitting rating.")

@router.get("/ratings/by-did", response_model=PaginatedRatings, tags=["Ratings"])
def get_ratings_by_did(
    did: str = Query(..., description="Agent DID (Decentralized Identifier)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Retrieve ratings for an agent specified by DID from the main database."""
    logging.info(f"Request received for GET /ratings/by-did: did={did}, page={page}, page_size={page_size}")
    try:
        agent_id = agent_id_from_did(db, did) # Uses main DB via helper
        if not agent_id:
            logging.warning(f"Agent not found for DID: {did} in get_ratings_by_did")
            raise HTTPException(status_code=404, detail="Agent with the specified DID not found")

        query = db.query(Rating).filter(Rating.agent_id == agent_id).order_by(Rating.timestamp.desc())
        all_ratings = query.all()
        # Add DID back for context in the response
        items = [ RatingOut.model_validate(r).model_copy(update={"did": did}) for r in all_ratings ]
        response = paginate(items, page=page, size=page_size)
        logging.info(f"Returning {len(response['items'])} ratings for DID {did}, page {page}.")
        return response
    except HTTPException: raise
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching ratings by DID {did}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error fetching ratings.")
    except Exception as e:
        logging.error(f"Unexpected error fetching ratings by DID {did}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching ratings.")

@router.get("/ratings/by-agent", response_model=PaginatedRatings, tags=["Ratings"])
def get_ratings_by_agent(
    agent_id: str = Query(..., description="Agent ID (internal database ID)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Retrieve ratings for an agent specified by internal ID from the main database."""
    logging.info(f"Request received for GET /ratings/by-agent: agent_id={agent_id}, page={page}, page_size={page_size}")
    try:
        # Check if agent exists first
        agent_exists = db.query(Agent.id).filter(Agent.id == agent_id).first() is not None
        if not agent_exists:
             logging.warning(f"Agent not found for ID: {agent_id} in get_ratings_by_agent")
             raise HTTPException(status_code=404, detail="Agent with the specified ID not found")

        query = db.query(Rating).filter(Rating.agent_id == agent_id).order_by(Rating.timestamp.desc())
        all_ratings = query.all()
        items = [RatingOut.model_validate(r) for r in all_ratings]
        response = paginate(items, page=page, size=page_size)
        logging.info(f"Returning {len(response['items'])} ratings for agent ID {agent_id}, page {page}.")
        return response
    except HTTPException: raise
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching ratings by agent ID {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error fetching ratings.")
    except Exception as e:
        logging.error(f"Unexpected error fetching ratings by agent ID {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching ratings.")

@router.get("/ratings/{_agent_id}", include_in_schema=False)
def _deprecated_ratings(*_):
    """Deprecated endpoint for fetching ratings."""
    raise HTTPException(status_code=410, detail="Deprecated. Use /ratings/by-agent or /ratings/by-did")

# --- Registry Endpoints (using main DB, depend on currently disabled sync) ---
@router.post("/registry-entry/", response_model=RegistryListSchema, tags=["Registry (Sync Disabled)"])
def registry_entry(
    limit: int = Body(10, embed=True, ge=1, le=50, description="Max number of entries"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of raw registry entries from the main database.
    NOTE (2025-04-19): Data relies on the RegistryEntry table, populated by a sync process
          which is currently disabled. May return empty results.
    """
    logging.info(f"Request received for POST /registry-entry: limit={limit}")
    try:
        rows = db.query(RegistryEntry).order_by(RegistryEntry.id).limit(limit).all()
        entries_data = []
        for r in rows:
             if hasattr(r, 'full_json') and isinstance(r.full_json, dict):
                 entries_data.append(r.full_json)
             else:
                 logging.warning(f"RegistryEntry {r.id} has missing or invalid 'full_json'. Skipping.")
        logging.info(f"Returning {len(entries_data)} raw registry entries.")
        return {"data": {"entries": entries_data}, "status": "success"}
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching registry entries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error fetching registry entries.")
    except Exception as e:
        logging.error(f"Unexpected error fetching registry entries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching registry entries.")

@router.get("/payment-information/", response_model=RegistryEntrySchema, tags=["Registry (Sync Disabled)"])
def payment_info(
    agentIdentifier: str = Query(..., min_length=3, description="Agent Identifier (Registry ID)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve raw registry information for a specific agent identifier from the main database.
    NOTE (2025-04-19): Data relies on the RegistryEntry table, populated by a sync process
          which is currently disabled. May return 'Not Found'.
    """
    logging.info(f"Request received for GET /payment-information: agentIdentifier={agentIdentifier}")
    try:
        row = db.get(RegistryEntry, agentIdentifier) # Use primary key lookup
        if not row:
            logging.warning(f"Registry entry not found for identifier: {agentIdentifier}")
            raise HTTPException(status_code=404, detail="Registry entry not found for the given identifier")

        if not hasattr(row, 'full_json') or not isinstance(row.full_json, dict):
             logging.error(f"RegistryEntry {agentIdentifier} has missing or invalid 'full_json'.")
             raise HTTPException(status_code=500, detail="Registry entry data format error")

        logging.info(f"Returning payment/registry info for identifier: {agentIdentifier}")
        return {"data": row.full_json, "status": "success"}
    except HTTPException: raise
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching payment info for {agentIdentifier}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error fetching payment info.")
    except Exception as e:
        logging.error(f"Unexpected error fetching payment info for {agentIdentifier}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching payment info.")

# --- Search Endpoint (uses models loaded in main.py) ---
@router.post("/search", response_model=QueryResponse, tags=["Search"])
async def search_agents_endpoint(
    query_req: QueryRequest,
    request: Request # Inject request to access app state
):
    """Performs semantic search using pre-loaded models and index."""
    # Check if search models are available (loaded during startup)
    if not request.app.state.search_enabled or \
       request.app.state.sentence_model is None or \
       request.app.state.faiss_index is None or \
       request.app.state.search_agents_list is None:
        logging.warning("Search endpoint called but search models are not available/loaded.")
        raise HTTPException(status_code=503, detail="Semantic search service unavailable.")

    logging.info(f"Search request: query='{query_req.query}', top_k={query_req.top_k}")
    # Retrieve models from application state
    model = request.app.state.sentence_model
    index = request.app.state.faiss_index
    # This list comes from search_model/agents.json (built from DB)
    agents_list_for_search = request.app.state.search_agents_list

    try:
        # 1. Encode query
        q_emb = model.encode([query_req.query], convert_to_numpy=True, show_progress_bar=False)
        # 2. Normalize query (must match index preparation)
        faiss.normalize_L2(q_emb)
        # 3. Search index
        scores, ids = index.search(q_emb, query_req.top_k)

        # 4. Process results
        results = []
        if ids.size > 0: # ids is numpy array, check size
            logging.debug(f"Search results: Indices={ids[0]}, Scores={scores[0]}")
            for i, idx in enumerate(ids[0]): # ids[0] holds indices for the first query
                if idx != -1: # Faiss returns -1 if index is invalid/not found
                    # Check index bounds for safety
                    if 0 <= idx < len(agents_list_for_search):
                        agent_data = agents_list_for_search[idx]
                        if isinstance(agent_data, dict):
                             result = AgentResult(
                                 # Prefer agentIdentifier if available, fallback to id
                                 id=agent_data.get("agentIdentifier", agent_data.get("id", f"missing_id_{idx}")),
                                 did=agent_data.get("did", "missing_did"),
                                 name=agent_data.get("name", "Unknown Agent"),
                                 description=agent_data.get("description", ""),
                                 score=float(scores[0][i]) # Corresponding score
                             )
                             results.append(result)
                             logging.debug(f"Found agent: {result.name} (Score: {result.score})")
                        else: logging.warning(f"Data at index {idx} in search agent list is not dict.")
                    else: logging.warning(f"Faiss index {idx} out of bounds for agent list (len={len(agents_list_for_search)}).")
                else: logging.warning(f"Invalid index -1 from Faiss search at position {i}.")

        logging.info(f"Search returning {len(results)} results for query '{query_req.query}'.")
        return QueryResponse(results=results)

    except Exception as e:
        logging.error(f"Error during search processing for query '{query_req.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during search processing.")

# --- Recommendations Endpoints (using recommend.db for storage, main DB for checks) ---

@router.post("/recommendations", response_model=RecommendationStatus, status_code=201, tags=["Recommendations"])
def add_recommendation(
    did: str = Body(..., embed=True, min_length=3, description="DID of agent being recommended"),
    db: Session = Depends(get_db),                     # Main DB session (to check Agent)
    rec_db: Optional[Session] = Depends(get_recommend_db) # Recommendation DB session (to write Recommendation log)
):
    """
    Records a recommendation event (DID + timestamp) in the separate recommendation database (recommend.db).
    Checks if the DID exists in the main agent database first.
    """
    logging.info(f"Request received for POST /recommendations: did={did}")
    # 1. Check agent existence using the main DB session
    if not agent_id_from_did(db, did):
        logging.warning(f"Attempted to log recommendation for non-existent DID: {did}")
        raise HTTPException(status_code=404, detail="Cannot recommend: Agent with specified DID not found in main DB.")

    # 2. Check if recommendation DB session is available
    if rec_db is None:
         logging.error("Recommendation database unavailable for POST /recommendations.")
         raise HTTPException(status_code=501, detail="Recommendation database service not available.")

    # 3. Add event log to 'recommendations' table in recommend.db
    try:
        rec_timestamp = datetime.now(tz=timezone.utc)
        # Create Recommendation ORM object (linked to RecommendBase)
        rec = Recommendation(did=did, timestamp=rec_timestamp)
        rec_db.add(rec)    # Use recommend DB session
        rec_db.commit()  # Use recommend DB session
        timestamp_str = rec_timestamp.isoformat()
        logging.info(f"Recommendation event logged successfully for DID: {did}")
        return RecommendationStatus(status="success", did=did, timestamp=timestamp_str)
    except SQLAlchemyError as e:
        rec_db.rollback() # Use recommend DB session
        logging.error(f"Database error saving recommendation event for DID {did}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save recommendation event.")
    except Exception as e:
        rec_db.rollback() # Use recommend DB session
        logging.error(f"Unexpected error saving recommendation event for DID {did}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error saving recommendation event.")


@router.get("/recommendations", response_model=RecommendationListResponse, tags=["Recommendations"])
def get_recommendations_log( # Renamed function for clarity
    rec_db: Optional[Session] = Depends(get_recommend_db) # Needs only recommendation DB session
):
    """
    Retrieves a list of unique DIDs from the recommendation events logged
    in the 'recommendations' table of the recommendation database (recommend.db).
    """
    logging.info("Request received for GET /recommendations (fetching distinct DIDs from log)")
    if rec_db is None:
        logging.error("Recommendation database unavailable for GET /recommendations.")
        raise HTTPException(status_code=501, detail="Recommendation database service not available.")

    try:
        # Query distinct DIDs from the 'recommendations' table
        logging.debug("Querying distinct DIDs from recommendations table (recommend.db).")
        # Recommendation model uses RecommendBase
        results = rec_db.query(Recommendation.did).distinct().all()
        # Extract DIDs from the list of tuples [(did1,), (did2,), ...]
        distinct_dids = [row[0] for row in results]
        logging.info(f"Found {len(distinct_dids)} distinct recommended DIDs in recommendations log.")

        return RecommendationListResponse(dids=distinct_dids)

    except SQLAlchemyError as e:
        logging.error(f"Database error fetching distinct recommendation DIDs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error retrieving recommendation DIDs.")
    except Exception as e:
        logging.error(f"Unexpected error fetching distinct recommendation DIDs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error retrieving recommendation DIDs.")

# --- End of route.py ---