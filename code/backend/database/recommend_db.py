# backend/database/recommend_db.py
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import RecommendBase

RECOMMEND_DB_PATH = Path(__file__).resolve().parents[2] / "recommend.db"
engine_recommend  = create_engine(f"sqlite:///{RECOMMEND_DB_PATH}", echo=False)
SessionRecommend  = sessionmaker(autocommit=False, autoflush=False, bind=engine_recommend)

def init_recommend_db() -> None:
    RecommendBase.metadata.create_all(bind=engine_recommend)