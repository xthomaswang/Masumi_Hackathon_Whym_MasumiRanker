#/backend/database/models.py
"""
Creates / initializes the standalone recommend.db database.
Call `init_recommend_db()` once at startup (e.g. in main.py).
"""

from pathlib import Path
from sqlalchemy import create_engine
from backend.database.models import RecommendBase

RECOMMEND_DB_PATH = Path(__file__).resolve().parents[2] / "recommend.db"
engine_recommend = create_engine(f"sqlite:///{RECOMMEND_DB_PATH}")

def init_recommend_db() -> None:
    """Ensure the recommend.db file and tables exist."""
    RecommendBase.metadata.create_all(bind=engine_recommend)
