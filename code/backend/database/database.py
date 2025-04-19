# backend/database/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Path to the SQLite database file (relative to project root)
DATABASE_URL = "sqlite:///./backend/database/masumi.db"

# Create the SQLAlchemy engine with thread check disabled
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for ORM models
Base = declarative_base()