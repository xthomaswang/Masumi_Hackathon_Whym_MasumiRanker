#/backend/database/models.py

"""
Database models for MasumiRanker
────────────────────────────────
• Agent            – core catalog entry (+ normalized USD price)
• Rating           – user feedback
• RegistryEntry    – full Masumi JSON blob (for loss‑less storage)
• RecommendedAgent – company‑curated “recommended” list (lives in its
                     own recommend.db so the Ops team can manage it
                     independently from the main application DB)
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    JSON,
    ForeignKey,
    Text,
    DateTime,
)
from datetime import datetime
from backend.database.database import Base


# ────────────────────────── Main Application DB ──────────────────────────
class Agent(Base):
    __tablename__ = "agents"
    id          = Column(String, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    category    = Column(String, index=True)
    description = Column(Text)
    did         = Column(String, unique=True, index=True)
    url         = Column(String)
    img_url     = Column(String, nullable=True)  
    price_usd   = Column(Float, default=0.0)
    avg_score   = Column(Float, default=0.0)
    num_ratings = Column(Integer, default=0)


class Rating(Base):
    """One row per user rating/comment."""
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"), index=True)
    user_id = Column(String)                  # may be null
    score = Column(Integer)
    comment = Column(Text)
    timestamp = Column(String)                # ISO‑8601
    hash = Column(String)                     # SHA‑256 for audit


class RegistryEntry(Base):
    """Full Masumi registry JSON for future reference."""
    __tablename__ = "registry"

    id = Column(String, primary_key=True, index=True)  # same as Agent.id
    full_json = Column(JSON)


# ───────────────────────────── Recommender DB ────────────────────────────
#
# This table is NOT stored in the main DB.  It’s created in a dedicated
# SQLite file (recommend.db) so that Business/Ops teams can edit it without
# touching the core application data.
#
from sqlalchemy.orm import declarative_base
RecommendBase = declarative_base()


class RecommendedAgent(RecommendBase):
    """
    List of hand‑picked agents that the company wants to highlight.
    Simple schema:
    • did    – primary key
    • rank   – lower number = higher priority (e.g. 1, 2, 3 …)
    • note   – optional editorial comment
    """
    __tablename__ = "recommended"

    did = Column(String, primary_key=True, index=True)
    rank = Column(Integer, default=0)
    note = Column(String, nullable=True)

class Recommendation(RecommendBase):
    __tablename__ = "recommendations"
    id        = Column(Integer, primary_key=True, autoincrement=True)
    did       = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)