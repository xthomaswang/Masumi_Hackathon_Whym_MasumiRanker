# backend/main.py
"""
Masumi Ranker Backend — main.py
Entry-point for the FastAPI application.

* Runs the API server
* Mounts static image files under "/images"
* Registers all routers under the "/api" prefix
* Initializes main (masumi.db) and recommendation (recommend.db) databases.
* Schedules periodic registry-sync jobs (Currently DISABLED)
* Loads semantic search models on startup.
"""

import sys
import logging
import json
import numpy as np
import faiss

from sentence_transformers import SentenceTransformer
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler

# --- Database Imports ---
# Import Base and engine for the main database
from backend.database.database import Base as MainBase, engine as main_engine
# Import the initializer for the recommendation database
from backend.database.recommend_db import init_recommend_db

# --- Router Import ---
from backend.routes.route import router as ranker_router

# --- Disabled Sync Import ---
# from backend.sync_registry_live import run_sync # Keep commented out

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# --- Determine Project Root and Paths ---
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except IndexError:
    logging.error("Error: Could not determine project root. Check script location.")
    sys.exit(1)

IMAGE_DIR = PROJECT_ROOT / "dataset" / "image"
SEARCH_MODEL_DIR = PROJECT_ROOT / "search_model" # Expect search models at project root

# --- Check Static Image Directory ---
if not IMAGE_DIR.is_dir():
    logging.error(f"Error: Static files directory does not exist: {IMAGE_DIR}")
    sys.exit(f"Error: Static files directory not found at {IMAGE_DIR}. Please create it.")
else:
    logging.info(f"Serving static images from: {IMAGE_DIR}")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Masumi Ranker API with Search & Recommendations",
    description="Backend service for the MasumiRanker project.",
    version="1.2.0", # Incremented version
)

# --- Define Constants for Search Models ---
MODEL_DIR_NAME = "search_model"
AGENTS_FILE_NAME = "agents.json"
INDEX_FILE_NAME = "index.faiss"
TRANSFORMER_MODEL_NAME = "all-MiniLM-L6-v2"

# --- Startup Event: Load Search Models ---
@app.on_event("startup")
def load_search_models():
    """Load semantic search models and data into app.state on startup."""
    logging.info("Attempting to load semantic search models...")
    search_model_path = PROJECT_ROOT / MODEL_DIR_NAME
    agents_path = search_model_path / AGENTS_FILE_NAME
    index_path = search_model_path / INDEX_FILE_NAME
    model_name = TRANSFORMER_MODEL_NAME

    # Initialize state
    app.state.search_enabled = False
    app.state.search_agents_list = None
    app.state.faiss_index = None
    app.state.sentence_model = None

    try:
        if not search_model_path.is_dir() or not agents_path.is_file() or not index_path.is_file():
             logging.error(f"Search model files not found in {search_model_path}. Semantic search disabled. Run build script.")
             return

        logging.info(f"Loading agent metadata for search from {agents_path}...")
        with open(agents_path, "r", encoding="utf-8") as f:
            app.state.search_agents_list = json.load(f)

        logging.info(f"Loading Faiss index from {index_path}...")
        app.state.faiss_index = faiss.read_index(str(index_path))

        logging.info(f"Loading Sentence Transformer model '{model_name}'...")
        app.state.sentence_model = SentenceTransformer(model_name)

        if not isinstance(app.state.search_agents_list, list):
             raise ValueError("Loaded agent data for search is not a list.")
        if app.state.faiss_index.ntotal != len(app.state.search_agents_list):
             logging.warning(f"Search Model Mismatch! Index vectors ({app.state.faiss_index.ntotal}) != agents loaded ({len(app.state.search_agents_list)}).")

        app.state.search_enabled = True
        logging.info("Semantic search models loaded successfully and search is enabled.")
        logging.info(f"Faiss index contains {app.state.faiss_index.ntotal} vectors.")

    except Exception as e:
        logging.error(f"Failed to load semantic search models: {e}", exc_info=True)
        app.state.search_enabled = False # Ensure flag is false on error


# --- Startup Event: Initialize Databases ---
@app.on_event("startup")
def initialize_databases():
    """Create database tables if they don't exist."""
    # Create main DB tables (using MainBase and main_engine)
    try:
        logging.info("Checking/creating main database tables (masumi.db)...")
        MainBase.metadata.create_all(bind=main_engine)
        logging.info("Main database tables checked/created successfully.")
    except Exception as e:
        logging.error(f"Error creating main database tables: {e}", exc_info=True)
        # Decide if app should proceed if main DB fails - likely should stop
        # sys.exit("Main DB table creation failed.")

    # Create recommendation DB tables (using RecommendBase via init_recommend_db)
    try:
        init_recommend_db() # This function logs its own messages
    except Exception as e:
        # Log again here in main context if needed
        logging.error(f"Initialization call for recommendation database failed: {e}", exc_info=True)
        # Decide if app should proceed if recommend DB fails

# --- Startup Event: Configure Background Scheduler (Sync Disabled) ---
scheduler = BackgroundScheduler(daemon=True)

@app.on_event("startup")
def start_scheduler():
    """
    Initializes background tasks. Sync is disabled.
    """
    global scheduler
    logging.info("Configuring background tasks (Sync Disabled)...")
    # --- Masumi Sync Disabled ---
    # scheduler.add_job(run_sync, "interval", minutes=30, id="run_sync_job")
    # --- Add other jobs if needed ---

    if scheduler.get_jobs():
        try:
            scheduler.start()
            logging.info("Background scheduler started with active jobs.")
        except Exception as e:
            logging.error(f"Failed to start background scheduler: {e}", exc_info=True)
    else:
        logging.info("Background scheduler initialized, but no active jobs are scheduled.")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_origin_regex=r"^https://.*\.ngrok-free\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount Static Files ---
app.mount(
    "/images",
    StaticFiles(directory=str(IMAGE_DIR)),
    name="images",
)

# --- Include API Routers ---
# Prefix is defined here for all routes in routes/route.py
app.include_router(ranker_router, prefix="/api")

# --- Root Health Check ---
@app.get("/", tags=["Meta"])
def root() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"message": "MasumiRanker backend with Search and Recommendations is running."}

# --- Shutdown Event Handler ---
@app.on_event("shutdown")
def shutdown_event():
    """Handle application shutdown."""
    global scheduler
    logging.info("Shutting down application...")
    # Shutdown scheduler
    try:
        if scheduler.running:
            scheduler.shutdown()
            logging.info("Background scheduler successfully shut down.")
        else:
            logging.info("Background scheduler was not running.")
    except Exception as e:
        logging.error(f"Error shutting down scheduler: {e}", exc_info=True)
    logging.info("Application shutdown complete.")

# --- Main Execution Block ---
if __name__ == "__main__":
    import uvicorn
    logging.info(f"Starting Uvicorn server...")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True, # Use reload only for development
        log_level="info"
    )