# backend/main.py
"""
Masumi Ranker Backend — main.py
Entry‑point for the FastAPI application.

* Runs the API server
* Registers all routers under the "/api" prefix
* Schedules periodic registry‑sync jobs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from backend.database.recommend_db import init_recommend_db
from backend.database.database import Base, engine
from backend.routes.route import router as ranker_router
from backend.sync_registry_live import run_sync

init_recommend_db()

app = FastAPI(
    title="Masumi Ranker API",
    description="Backend service for the MasumiRanker hackathon project",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS (open to all origins — hackathon‑friendly; tighten later if needed)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Create DB tables (SQLAlchemy will no‑op if they already exist)
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Register all API routes under the common "/api" prefix
# ---------------------------------------------------------------------------
app.include_router(ranker_router, prefix="/api")

# ---------------------------------------------------------------------------
# Meta / health‑check endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    """Simple health‑check route."""
    return {"message": "MasumiRanker backend is running."}

# ---------------------------------------------------------------------------
# Background scheduler — sync Masumi registry periodically
# ---------------------------------------------------------------------------
@app.on_event("startup")
def start_scheduler() -> None:
    """Kick off the initial registry sync + recurring job."""
    run_sync()  # initial sync on startup

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_sync, "interval", minutes=30)
    scheduler.start()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
