# backend/database/models.py

from sqlalchemy import (
    Column, String, Integer, Float, JSON, ForeignKey, Text, DateTime
)
from datetime import datetime
# Import Base for the main application database
from .database import Base
# Import declarative_base to create a separate Base for the recommendation database
from sqlalchemy.orm import declarative_base

# ---------------- Main Application DB Models (inherit from Base) ----------------

class Agent(Base):
    """ Core agent catalog entry in the main database (e.g., masumi.db) """
    __tablename__ = "agents"
    id          = Column(String, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    category    = Column(String, index=True)
    description = Column(Text)
    did         = Column(String, unique=True, index=True)
    url         = Column(String)
    img_url     = Column(String, nullable=True) # Corrected attribute name
    price_usd   = Column(Float, default=0.0)
    avg_score   = Column(Float, default=0.0)
    num_ratings = Column(Integer, default=0)


class Rating(Base):
    """ User feedback/rating stored in the main database. """
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"), index=True)
    user_id = Column(String, nullable=True) # User identifier might be optional
    score = Column(Integer)
    comment = Column(Text, nullable=True) # Comments are optional
    timestamp = Column(String) # Store as ISO 8601 string
    hash = Column(String) # Optional hash for audit


class RegistryEntry(Base):
    """ Stores the full, original Masumi registry JSON blob in the main database. """
    __tablename__ = "registry"
    id = Column(String, primary_key=True, index=True) # Corresponds to Agent.id/agentIdentifier
    full_json = Column(JSON)


# ------------- Recommendation DB Models (inherit from RecommendBase) -------------

# Create a separate Base for models residing in recommend.db
RecommendBase = declarative_base()

class RecommendedAgent(RecommendBase):
    """
    Represents the curated list of hand-picked agents.
    Stored in the separate recommendation database (recommend.db).
    """
    __tablename__ = "recommended" # Table name for the curated list

    did = Column(String, primary_key=True, index=True) # Agent DID is the primary key
    rank = Column(Integer, default=0, index=True) # Lower rank means higher priority
    note = Column(String, nullable=True) # Optional editorial note

class Recommendation(RecommendBase):
    """
    Represents a log entry for when an agent recommendation action occurs.
    Stored in the separate recommendation database (recommend.db).
    """
    __tablename__ = "recommendations" # Table name for the event log
    id        = Column(Integer, primary_key=True, autoincrement=True) # Auto-incrementing primary key for the log entry
    did       = Column(String, nullable=False, index=True) # The DID of the agent recommended
    timestamp = Column(DateTime, default=datetime.utcnow, index=True) # Timestamp of the recommendation event