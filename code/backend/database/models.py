# backend/database/models.py
from sqlalchemy import Column, String, Integer, Float, JSON
from backend.database.database import Base

class Agent(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    category = Column(String)
    description = Column(String)
    did = Column(String)
    url = Column(String)
    avg_score = Column(Float, default=0.0)
    num_ratings = Column(Integer, default=0)

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, index=True)
    user_id = Column(String)
    score = Column(Integer)
    comment = Column(String)
    timestamp = Column(String)
    hash = Column(String)

# NEW – full Masumi registry JSON blob
class RegistryEntry(Base):
    __tablename__ = "registry"
    id = Column(String, primary_key=True, index=True)   # NFT id / cuid / fallback
    full_json = Column(JSON)                            # store entire entry
