# backend/database/database.py

import logging
from pathlib import Path  # <-- Import Path for path manipulation
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Calculate Absolute Path for the Database File ---

# 1. Get the directory where this file (database.py) is located
#    Path(__file__).resolve() gets the absolute path of this script
#    .parent gets the directory containing it (e.g., .../code/backend/database)
CURRENT_DIR = Path(__file__).resolve().parent

# 2. Define the database filename
DB_FILENAME = "masumi.db"

# 3. Construct the absolute path to the database file
#    It resides in the same directory as this script.
DB_ABSOLUTE_PATH = CURRENT_DIR / DB_FILENAME

# 4. Construct the DATABASE_URL for SQLite using the absolute path.
#    The format starts with 'sqlite:///' followed by the absolute path.
#    .resolve() ensures the path is absolute and cleans it up (e.g., resolves ..).
DATABASE_URL = f"sqlite:///{DB_ABSOLUTE_PATH.resolve()}"

# --- Configure Logging (Optional but helpful for debugging) ---
# Ensure logging is configured somewhere (e.g., in main.py or here)
# If configuring here, do it before the first logging call.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s")
logging.info(f"Main database configured at absolute path: {DATABASE_URL}")

# --- SQLAlchemy Setup ---

# Create the SQLAlchemy engine using the absolute DATABASE_URL
engine = create_engine(
    DATABASE_URL,
    # connect_args is specific to SQLite to allow usage across threads in FastAPI
    connect_args={"check_same_thread": False}
)

# Create a configured "Session" class (Session factory)
# Use this SessionLocal() to create session instances in your dependencies (get_db)
SessionLocal = sessionmaker(
    autocommit=False, # Transactions are not automatically committed
    autoflush=False,  # Objects are not automatically flushed to DB before queries
    bind=engine       # Bind the session factory to our engine
)

# Create a Base class for declarative class definitions (ORM models)
# Your models in models.py should inherit from this Base
Base = declarative_base()