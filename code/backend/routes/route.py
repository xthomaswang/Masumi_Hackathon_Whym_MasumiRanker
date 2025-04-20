# backend/routes/route.py
"""
API endpoint definitions for the MasumiRanker backend.
Mounted under the /api prefix in main.py.
Includes endpoints for Agents, Ratings, Search, Recommendations,
Review Summarization, and Registry data (Registry sync currently disabled).
"""

import logging
import json
import numpy as np
import faiss
from pathlib import Path
from datetime import datetime, timezone
import hashlib
from typing import List, Dict, Any, Generator, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Body # Added Body import back
from pydantic import BaseModel, Field, ConfigDict # Assuming Pydantic v2+
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import distinct # For querying distinct DIDs

# --- Database and Model Imports ---
# Import Session factory for the main database (masumi.db)
from backend.database.database import SessionLocal
# Import all SQLAlchemy models defined in models.py
# Assumes Agent, Rating, RegistryEntry use main Base
# Assumes Recommendation, RecommendedAgent use RecommendBase
from backend.database.models import Agent, Rating, RegistryEntry, Recommendation
try:
    # Import the separate Session factory for the recommendation database (recommend.db)
    from backend.database.recommend_db import SessionRecommend
except ImportError:
    SessionRecommend = None # Gracefully handle if recommend_db setup doesn't exist
    logging.warning("Recommendation DB session factory (SessionRecommend) not found or import failed.")

# --- Router Setup ---
# API endpoints defined here will be included with a prefix (e.g., /api) in main.py
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
    """FastAPI dependency to get a main database (masumi.db) session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_recommend_db() -> Optional[Generator[Session, None, None]]:
    """
    FastAPI dependency to get a recommendation database (recommend.db) session.
    Yields None if SessionRecommend is not available.
    """
    if SessionRecommend:
        db = SessionRecommend()
        try:
            yield db
        finally:
            db.close()
    else:
        yield None

def agent_id_from_did(db: Session, did: str) -> Optional[str]:
    """Retrieve an agent's internal ID from its DID using the main database session."""
    try:
        agent = db.query(Agent.id).filter(Agent.did == did).first() # Query only ID for efficiency
        return agent.id if agent else None
    except SQLAlchemyError as e:
        logging.error(f"Database error finding agent by DID {did}: {e}", exc_info=True)
        # Let the calling endpoint handle the HTTPException
        raise HTTPException(status_code=500, detail="Database error retrieving agent by DID.")

def utc_iso() -> str:
    """Returns the current timestamp in UTC ISO 8601 format string."""
    return datetime.now(tz=timezone.utc).isoformat()

# --------------------- Pydantic Schemas ---------------------
# Define data structures for request validation and response serialization.

class AgentOut(BaseModel):
    """Schema for returning agent details to the client."""
    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = ""
    did: str
    url: Optional[str] = None
    price_usd: Optional[float] = 0.0
    avg_score: Optional[float] = 0.0
    num_ratings: Optional[int] = 0
    img_url: Optional[str] = None # Dynamically generated URL path

    model_config = ConfigDict(from_attributes=True) # Enable ORM mode (Pydantic V2)
    # For Pydantic V1 use:
    # class Config:
    #     orm_mode = True

class RatingIn(BaseModel):
    """Schema for validating incoming rating submissions."""
    agent_id: str # The internal ID of the agent being rated
    user_id: Optional[str] = None # Optional identifier for the rating user
    score: int = Field(..., ge=1, le=5, description="Rating score (must be between 1 and 5)")
    comment: str = Field("", max_length=1000, description="Optional user comment (max 1000 chars)")

class RatingOut(RatingIn):
    """Schema for returning rating details, including server-generated fields."""
    timestamp: str # ISO 8601 timestamp string
    hash: str # SHA-256 hash for auditability
    did: Optional[str] = None # Agent DID, optionally added for context

    model_config = ConfigDict(from_attributes=True)
    # For Pydantic V1 use:
    # class Config:
    #     orm_mode = True

class PaginatedAgents(BaseModel):
    """Schema for paginated responses containing a list of agents."""
    items: List[AgentOut]
    page: int
    page_size: int
    total_items: int

class PaginatedRatings(BaseModel):
    """Schema for paginated responses containing a list of ratings."""
    items: List[RatingOut]
    page: int
    page_size: int
    total_items: int

class RegistryListSchema(BaseModel):
    """Schema for returning a list of raw registry entries (feature currently disabled)."""
    data: Dict[str, List[Dict[str, Any]]] # Structure depends on the external Masumi API
    status: str

class RegistryEntrySchema(BaseModel):
    """Schema for returning a single raw registry entry (feature currently disabled)."""
    data: Dict[str, Any] # Structure depends on the external Masumi API
    status: str

class RecommendationStatus(BaseModel):
    """Schema for the confirmation response after POSTing a recommendation event."""
    status: str
    did: str
    timestamp: str # ISO 8601 timestamp string

class QueryRequest(BaseModel):
    """Schema for validating incoming semantic search requests."""
    query: str = Field(..., description="The natural language query string to search for.")
    top_k: int = Field(3, ge=1, le=50, description="The maximum number of similar agents to return.")

class AgentResult(BaseModel):
    """Schema for representing a single agent within search results."""
    id: str # agentIdentifier or internal id from the indexed agents data
    did: str
    name: str
    description: Optional[str] = ""
    score: float # Similarity score (higher is better for cosine/IP index)

class QueryResponse(BaseModel):
    """Schema for the semantic search API response."""
    results: List[AgentResult]

class RecommendationListResponse(BaseModel):
    """Schema for returning the list of distinct DIDs from recommendation events."""
    dids: List[str]

class AgentSummaryResponse(BaseModel):
    """Schema for returning the generated agent review summary."""
    agent_id: str
    summary: str

# --------------------- Image URL Helper ---------------------

def _attach_img(agent_obj: Agent) -> AgentOut:
    """
    Helper function to create an AgentOut Pydantic model from an Agent ORM object,
    correctly formatting the 'img_url' field as a web-accessible path.
    """
    try:
        # Validate and convert the SQLAlchemy Agent object to an AgentOut Pydantic model
        out = AgentOut.model_validate(agent_obj)
        # Check if the agent record has an associated image reference in the database
        if agent_obj.img_url:
            # Assume img_url stores filename or relative path; extract filename safely
            filename = Path(agent_obj.img_url).name
            # Construct the URL path served by the static files middleware in main.py
            out.img_url = f"/images/{filename}"
        else:
            # Ensure the output img_url is None if not present in the database
            out.img_url = None
        return out
    except Exception as e:
        # Log details if processing fails for an agent
        logging.error(f"Error processing agent image data (Agent ID: {getattr(agent_obj, 'id', 'N/A')}): {e}", exc_info=True)
        # Raise exception to be handled by the calling endpoint, resulting in a 500 response
        raise HTTPException(status_code=500, detail="Internal server error while processing agent image data.")

# --------------------- API Endpoints ---------------------

# --- Agent Endpoints (using main DB: masumi.db) ---
@router.get("/agents", response_model=PaginatedAgents, tags=["Agents"])
def get_agents(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(20, ge=1, le=100, description="Number of agents per page (1-100)"),
    db: Session = Depends(get_db) # Dependency injects the main DB session
):
    """
    Retrieve a paginated list of agents from the main database (masumi.db).
    Agents are sorted by average rating score in descending order by default.
    """
    logging.info(f"Request received for GET /agents: page={page}, page_size={page_size}")
    try:
        # Query all agents, ordered by score
        db_agents = db.query(Agent).order_by(Agent.avg_score.desc()).all()
        # Process each agent to format image URL and validate output schema
        items = [_attach_img(a) for a in db_agents]
        # Paginate the results
        response = paginate(items, page=page, size=page_size)
        logging.info(f"Returning {len(response['items'])} agents for page {page}.")
        return response
    except HTTPException: raise # Re-raise HTTPExceptions from helpers (e.g., _attach_img)
    except SQLAlchemyError as e:
        logging.error(f"Database error while fetching agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="A database error occurred while fetching agents.")
    except Exception as e:
        logging.error(f"Unexpected error while fetching agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred while fetching agents.")

@router.get("/agents/{agent_id}", response_model=AgentOut, tags=["Agents"])
def read_agent(
    agent_id: str, # Agent ID from the URL path
    db: Session = Depends(get_db)
):
    """
    Retrieve details for a specific agent by its internal database ID
    from the main database (masumi.db).
    """
    logging.info(f"Request received for GET /agents/{agent_id}")
    try:
        # Use db.get for efficient primary key lookup
        db_agent = db.get(Agent, agent_id)
        if not db_agent:
            logging.warning(f"Agent with ID '{agent_id}' not found.")
            raise HTTPException(status_code=404, detail="Agent not found")
        # Process the agent data (including image URL) for the response
        response = _attach_img(db_agent)
        logging.info(f"Returning details for agent ID: {agent_id}")
        return response
    except HTTPException: raise # Re-raise 404 or 500 from _attach_img
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="A database error occurred while fetching the agent.")
    except Exception as e:
        logging.error(f"Unexpected error fetching agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred while fetching the agent.")


# --- Rating Endpoints (using main DB: masumi.db) ---
@router.post("/ratings", response_model=RatingOut, status_code=201, tags=["Ratings"])
def submit_rating(p: RatingIn, db: Session = Depends(get_db)):
    """
    Submits a new rating (score and optional comment) for an agent.
    Updates the agent's average score and rating count in the main database.
    """
    logging.info(f"Request received for POST /ratings for agent_id: {p.agent_id}")
    try:
        # Fetch the agent being rated
        agent = db.get(Agent, p.agent_id)
        if not agent:
            logging.warning(f"Attempted to rate non-existent agent ID: {p.agent_id}")
            raise HTTPException(status_code=400, detail="Invalid agent_id provided.")

        timestamp = utc_iso()
        # Create a hash for potential audit purposes
        rating_hash_content = f"{p.agent_id}{p.user_id or ''}{timestamp}{p.score}{p.comment}"
        rating_hash = hashlib.sha256(rating_hash_content.encode()).hexdigest()

        # Create new Rating ORM object
        new_rating = Rating(**p.model_dump(), timestamp=timestamp, hash=rating_hash)
        db.add(new_rating)

        # Update the associated Agent's aggregated score data safely
        current_total_score = (agent.avg_score or 0.0) * (agent.num_ratings or 0)
        new_num_ratings = (agent.num_ratings or 0) + 1
        agent.avg_score = round((current_total_score + p.score) / new_num_ratings, 2)
        agent.num_ratings = new_num_ratings
        logging.debug(f"Updating agent {p.agent_id} rating aggregates: score={agent.avg_score}, num_ratings={agent.num_ratings}")

        db.commit() # Commit transaction
        db.refresh(new_rating) # Refresh to get any DB-generated fields (like autoincrement ID)
        logging.info(f"Rating submitted successfully for agent ID: {p.agent_id}")
        # Return the details of the created rating
        return RatingOut.model_validate(new_rating)

    except HTTPException: raise
    except SQLAlchemyError as e:
        db.rollback() # Rollback transaction on DB error
        logging.error(f"Database error submitting rating for agent {p.agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while submitting rating.")
    except Exception as e:
        db.rollback() # Rollback on any other error
        logging.error(f"Unexpected error submitting rating for agent {p.agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error occurred while submitting rating.")

@router.get("/ratings/by-did", response_model=PaginatedRatings, tags=["Ratings"])
def get_ratings_by_did(
    did: str = Query(..., description="Agent DID (Decentralized Identifier)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Retrieve a paginated list of ratings for an agent specified by its DID."""
    logging.info(f"Request received for GET /ratings/by-did: did={did}, page={page}, page_size={page_size}")
    try:
        agent_id = agent_id_from_did(db, did) # Find internal ID from DID
        if not agent_id:
            logging.warning(f"Agent not found for DID: {did} in get_ratings_by_did")
            raise HTTPException(status_code=404, detail="Agent with the specified DID not found")

        # Query ratings associated with the found agent_id
        query = db.query(Rating).filter(Rating.agent_id == agent_id).order_by(Rating.timestamp.desc())
        all_ratings = query.all()
        # Convert to Pydantic model, adding the DID for context
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
    agent_id: str = Query(..., description="Agent's internal database ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Retrieve a paginated list of ratings for an agent specified by its internal ID."""
    logging.info(f"Request received for GET /ratings/by-agent: agent_id={agent_id}, page={page}, page_size={page_size}")
    try:
        # Verify the agent actually exists
        agent_exists = db.query(Agent.id).filter(Agent.id == agent_id).first() is not None
        if not agent_exists:
             logging.warning(f"Agent not found for ID: {agent_id} in get_ratings_by_agent")
             raise HTTPException(status_code=404, detail="Agent with the specified ID not found")

        # Query ratings associated with the agent_id
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
    """Deprecated endpoint. Use /ratings/by-agent or /ratings/by-did instead."""
    logging.warning("Deprecated endpoint /ratings/{_agent_id} accessed.")
    raise HTTPException(status_code=410, detail="This endpoint is deprecated. Use /ratings/by-agent?agent_id=<id> or /ratings/by-did?did=<did>")

# --- Registry Endpoints (Note: Linked to currently disabled external sync) ---
@router.post("/registry-entry/", response_model=RegistryListSchema, tags=["Registry (Sync Disabled)"])
def registry_entry(
    limit: int = Body(10, embed=True, ge=1, le=50, description="Maximum number of raw entries to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of raw registry entries stored in the main database.
    NOTE (2025-04-19): The underlying data (RegistryEntry table) depends on an external
          synchronization process which is currently disabled in main.py.
          This endpoint may return empty or stale data.
    """
    logging.info(f"Request received for POST /registry-entry: limit={limit}")
    try:
        rows = db.query(RegistryEntry).order_by(RegistryEntry.id).limit(limit).all()
        entries_data = []
        for r in rows:
             # Safely access and check the stored JSON data
             if hasattr(r, 'full_json') and isinstance(r.full_json, dict):
                 entries_data.append(r.full_json)
             else:
                 logging.warning(f"RegistryEntry {getattr(r, 'id', 'N/A')} has missing or invalid 'full_json' data. Skipping.")
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
    agentIdentifier: str = Query(..., min_length=3, description="Registry ID of the agent"),
    db: Session = Depends(get_db)
):
    """
    Retrieve raw registry information for a specific agent identifier from the main database.
    NOTE (2025-04-19): The underlying data (RegistryEntry table) depends on an external
          synchronization process which is currently disabled in main.py.
          This endpoint may return 'Not Found' or stale data.
    """
    logging.info(f"Request received for GET /payment-information: agentIdentifier={agentIdentifier}")
    try:
        # Use db.get for primary key lookup, assuming agentIdentifier is the PK ('id')
        row = db.get(RegistryEntry, agentIdentifier)
        if not row:
            logging.warning(f"Registry entry not found for identifier: {agentIdentifier}")
            raise HTTPException(status_code=404, detail="Registry entry not found for the given identifier")

        # Validate the stored JSON data before returning
        if not hasattr(row, 'full_json') or not isinstance(row.full_json, dict):
             logging.error(f"RegistryEntry {agentIdentifier} has missing or invalid 'full_json' format in database.")
             # Return 500 as this indicates a data integrity issue
             raise HTTPException(status_code=500, detail="Stored registry entry data has an invalid format.")

        logging.info(f"Returning payment/registry info for identifier: {agentIdentifier}")
        return {"data": row.full_json, "status": "success"}
    except HTTPException: raise # Re-raise 404 or 500
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching payment info for {agentIdentifier}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error fetching payment information.")
    except Exception as e:
        logging.error(f"Unexpected error fetching payment info for {agentIdentifier}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching payment information.")

# --- Search Endpoint (uses models loaded via app.state in main.py) ---
@router.post("/search", response_model=QueryResponse, tags=["Search"])
async def search_agents_endpoint(
    query_req: QueryRequest, # Request body validated by Pydantic
    request: Request         # FastAPI request object to access application state
):
    """
    Performs semantic vector search for agents based on the provided query string,
    using pre-loaded Sentence Transformer model and Faiss index.
    """
    # Retrieve pre-loaded models and data from application state (set in main.py)
    summarizer_instance = getattr(request.app.state, 'summarizer', None) # Keep for consistency
    search_enabled = getattr(request.app.state, 'search_enabled', False)
    model = getattr(request.app.state, 'sentence_model', None)
    index = getattr(request.app.state, 'faiss_index', None)
    agents_list_for_search = getattr(request.app.state, 'search_agents_list', None) # List of dicts from search_model/agents.json

    # Check if search functionality is ready
    if not search_enabled or model is None or index is None or agents_list_for_search is None:
        logging.warning("Search endpoint called but search models/data are not available/loaded.")
        raise HTTPException(status_code=503, detail="Semantic search service is currently unavailable.")

    logging.info(f"Processing search request: query='{query_req.query}', top_k={query_req.top_k}")

    try:
        # 1. Encode the incoming query string into a vector embedding
        # Note: model.encode might be CPU/GPU intensive
        q_emb = model.encode([query_req.query], convert_to_numpy=True, show_progress_bar=False)

        # 2. Normalize the query embedding (L2 normalization)
        # This is crucial for IndexFlatIP to perform cosine similarity search.
        faiss.normalize_L2(q_emb)

        # 3. Search the Faiss index for nearest neighbors
        # Returns distances (inner product scores for IndexFlatIP) and indices
        scores, ids = index.search(q_emb, query_req.top_k)

        # 4. Process the search results
        results = []
        if ids.size > 0: # Check if Faiss returned any indices
            logging.debug(f"Raw search results: Indices={ids[0]}, Scores={scores[0]}")
            # Iterate through the indices and scores found for the first (only) query
            for i, idx in enumerate(ids[0]):
                # Faiss might return -1 for indices if k > number of items
                if idx != -1:
                    # Safety check: Ensure the index is within the bounds of our agent list
                    if 0 <= idx < len(agents_list_for_search):
                        agent_data = agents_list_for_search[idx] # Get agent metadata dict
                        if isinstance(agent_data, dict):
                             # Create the result object using Pydantic schema
                             result = AgentResult(
                                 # Use agentIdentifier field if available, otherwise fallback to id
                                 id=agent_data.get("agentIdentifier", agent_data.get("id", f"missing_id_at_index_{idx}")),
                                 did=agent_data.get("did", "missing_did"), # Provide default if missing
                                 name=agent_data.get("name", "Unknown Agent"),
                                 description=agent_data.get("description", ""),
                                 score=float(scores[0][i]) # Get the corresponding similarity score
                             )
                             results.append(result)
                             logging.debug(f"Adding search result: {result.name} (Score: {result.score:.4f})")
                        else:
                            logging.warning(f"Data at index {idx} in search agent list is not a dictionary. Skipping.")
                    else:
                        # This indicates an inconsistency between the index and the agent list file
                        logging.warning(f"Faiss returned out-of-bounds index {idx}. Max index is {len(agents_list_for_search)-1}. Skipping.")
                else:
                     # This can happen if k > index.ntotal or for other Faiss reasons
                     logging.warning(f"Faiss returned invalid index -1 at search result position {i}. Skipping.")

        logging.info(f"Search completed. Returning {len(results)} results for query '{query_req.query}'.")
        return QueryResponse(results=results)

    except Exception as e:
        # Catch potential errors during encoding or Faiss search
        logging.error(f"Error during search processing for query '{query_req.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error occurred during search processing.")

# --- Recommendations Endpoints (using recommend.db for storage, main DB for checks) ---

@router.post("/recommendations", response_model=RecommendationStatus, status_code=201, tags=["Recommendations"])
def add_recommendation(
    did: str = Body(..., embed=True, min_length=3, description="DID of the agent being recommended"),
    db: Session = Depends(get_db),                     # Main DB session (to check Agent validity)
    rec_db: Optional[Session] = Depends(get_recommend_db) # Recommendation DB session (to write event log)
):
    """
    Records a recommendation event (DID + timestamp) in the separate
    recommendation database (recommend.db -> 'recommendations' table).
    It first verifies that the agent DID exists in the main database.
    """
    logging.info(f"Request received for POST /recommendations: did={did}")
    # 1. Validate Agent DID using the main database
    if not agent_id_from_did(db, did): # Checks agents table in masumi.db
        logging.warning(f"Attempted to log recommendation for non-existent DID: {did}")
        raise HTTPException(status_code=404, detail="Cannot recommend: Agent with specified DID not found in main database.")

    # 2. Ensure the recommendation database session is available
    if rec_db is None:
         logging.error("Recommendation database session unavailable for POST /recommendations.")
         raise HTTPException(status_code=501, detail="Recommendation database service is not available.") # 501 = Not Implemented

    # 3. Add the recommendation event to the 'recommendations' table in recommend.db
    try:
        rec_timestamp = datetime.now(tz=timezone.utc)
        # Create ORM object using Recommendation model (linked to RecommendBase)
        rec_event = Recommendation(did=did, timestamp=rec_timestamp)
        rec_db.add(rec_event)    # Add to recommendation session
        rec_db.commit()          # Commit recommendation session
        timestamp_str = rec_timestamp.isoformat()
        logging.info(f"Recommendation event logged successfully in recommend.db for DID: {did}")
        # Return success status
        return RecommendationStatus(status="success", did=did, timestamp=timestamp_str)
    except SQLAlchemyError as e:
        rec_db.rollback() # Rollback recommendation session on error
        logging.error(f"Database error saving recommendation event for DID {did} to recommend.db: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save recommendation event due to database error.")
    except Exception as e:
        rec_db.rollback() # Rollback recommendation session on error
        logging.error(f"Unexpected error saving recommendation event for DID {did}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error occurred while saving recommendation event.")


@router.get("/recommendations", response_model=RecommendationListResponse, tags=["Recommendations"])
def get_recommendations_log( # Renamed function to reflect current logic
    rec_db: Optional[Session] = Depends(get_recommend_db) # Depends only on recommendation DB session
):
    """
    Retrieves a list of unique agent DIDs that have been previously logged
    via the POST /recommendations endpoint. Reads from the 'recommendations'
    table in the recommendation database (recommend.db).
    """
    logging.info("Request received for GET /recommendations (fetching distinct DIDs from event log)")
    # Check if recommendation DB session is available
    if rec_db is None:
        logging.error("Recommendation database unavailable for GET /recommendations.")
        raise HTTPException(status_code=501, detail="Recommendation database service not available.")

    try:
        # Query distinct DIDs from the 'recommendations' table in recommend.db
        logging.debug("Querying distinct DIDs from recommendations table (recommend.db).")
        # Recommendation model uses RecommendBase
        # Query the 'did' column, apply distinct, fetch all results
        results = rec_db.query(Recommendation.did).distinct().all()
        # The result is a list of tuples, e.g., [('did1',), ('did2',)]; extract the first element of each tuple.
        distinct_dids = [row[0] for row in results]
        logging.info(f"Found {len(distinct_dids)} distinct recommended DIDs in the event log (recommend.db).")

        # Return the list of DIDs in the specified response format
        return RecommendationListResponse(dids=distinct_dids)

    except SQLAlchemyError as e:
        logging.error(f"Database error fetching distinct recommendation DIDs from recommend.db: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error retrieving recommendation DIDs.")
    except Exception as e:
        logging.error(f"Unexpected error fetching distinct recommendation DIDs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error retrieving recommendation DIDs.")

# --- End of route.py ---