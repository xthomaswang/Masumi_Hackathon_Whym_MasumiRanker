# backend/database/models.py

from sqlalchemy import Column, String, Integer, Float
from backend.database.database import Base

class Agent(Base):
    __tablename__ = "agents"

    # Unique identifier for each agent
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    category = Column(String)
    description = Column(String)
    did = Column(String)
    url = Column(String)
    # Average score computed from ratings
    avg_score = Column(Float, default=0.0)
    # Number of times this agent has been rated
    num_ratings = Column(Integer, default=0)

class Rating(Base):
    __tablename__ = "ratings"

    # Auto-incremented primary key for each rating
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Foreign key linking to Agent.id
    agent_id = Column(String, index=True)
    # Identifier of the user who submitted the rating
    user_id = Column(String)
    # Rating score between 1 and 5
    score = Column(Integer)
    # Optional comment text
    comment = Column(String)
    # Timestamp when the rating was created
    timestamp = Column(String)
    # SHA-256 hash for audit verification
    hash = Column(String)