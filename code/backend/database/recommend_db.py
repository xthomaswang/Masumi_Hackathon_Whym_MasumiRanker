# backend/database/recommend_db.py

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Import RecommendBase defined in models.py
# This ensures both files use the same declarative base for recommend.db models
try:
    # Use relative import assuming models.py is in the same directory
    from .models import RecommendBase
except ImportError:
    # Fallback or error handling if structure is different or run standalone
    logging.error("Could not import RecommendBase from .models in recommend_db.py. Ensure models.py exists.")
    # You might need to redefine RecommendBase here if the import consistently fails in your setup,
    # but sharing the definition via models.py is cleaner.
    from sqlalchemy.orm import declarative_base
    RecommendBase = declarative_base()


# --- Calculate absolute path for recommend.db ---
# Store recommend.db in the same directory as this file (database/)
CURRENT_DIR = Path(__file__).resolve().parent
DB_FILENAME = "recommend.db" # Database file name
DB_ABSOLUTE_PATH = CURRENT_DIR / DB_FILENAME
RECOMMEND_DATABASE_URL = f"sqlite:///{DB_ABSOLUTE_PATH.resolve()}"

logging.info(f"Recommendation database configured at absolute path: {RECOMMEND_DATABASE_URL}")

# Create the SQLAlchemy engine for the recommendation database
recommend_engine = create_engine(
    RECOMMEND_DATABASE_URL,
    connect_args={"check_same_thread": False} # Required for SQLite with FastAPI/threading
)

# Create a configured "Session" class bound to the recommendation engine
SessionRecommend = sessionmaker(autocommit=False, autoflush=False, bind=recommend_engine)

# Initialization function to create tables defined by RecommendBase
def init_recommend_db():
    """Creates tables (recommended, recommendations) in recommend.db if they don't exist."""
    logging.info(f"Checking/creating tables for recommendation database: {RECOMMEND_DATABASE_URL}")
    try:
        # Use RecommendBase.metadata to create associated tables
        RecommendBase.metadata.create_all(bind=recommend_engine)
        logging.info("Recommendation database tables checked/created successfully.")
    except Exception as e:
        logging.error(f"Error creating recommendation database tables: {e}", exc_info=True)
        # Depending on requirements, you might want to raise the exception
        # raise