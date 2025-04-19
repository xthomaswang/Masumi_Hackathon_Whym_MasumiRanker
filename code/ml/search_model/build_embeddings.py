print("--- Executing build_embeddings.py with 'code.backend' imports ---")

import json
import numpy as np
import faiss
import os
import logging
import sys
from sentence_transformers import SentenceTransformer

# --- Add necessary imports for database access ---
# Adjust import paths based on where this script lives relative to the 'backend' package
# Assuming run from project root (parent of 'code')

try:
    from code.backend.database.database import SessionLocal
    from code.backend.database.models import Agent
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import SQLAlchemyError
except ImportError as e:
    import traceback 
    sys.exit(1)
    # --- END REPLACEMENT ---

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")


# --- Fetch Agent Data from Database ---
def get_agents_from_db() -> list[dict]:
    """Fetches all agents from the database and returns them as a list of dicts."""
    logging.info("Connecting to database and fetching agents...")
    db: Session = SessionLocal()
    agents_data = []
    try:
        # Query all agents from the database
        db_agents = db.query(Agent).all()
        logging.info(f"Fetched {len(db_agents)} agents from the database.")

        # Convert SQLAlchemy objects to dictionaries suitable for saving and embedding
        for agent_obj in db_agents:
            # Ensure essential fields exist for embedding and later lookup
            if agent_obj.name and agent_obj.description and agent_obj.did:
                agents_data.append({
                    # Include fields needed for generating text ('name', 'description')
                    "name": agent_obj.name,
                    "description": agent_obj.description,
                    # Include fields needed by the search API response ('did', 'id', etc.)
                    "did": agent_obj.did,
                    "id": agent_obj.id, # Assuming 'id' is the primary key used elsewhere
                    # Add other relevant fields if needed later by the search result display
                    "category": agent_obj.category,
                    "url": agent_obj.url,
                })
            else:
                 logging.warning(f"Skipping agent with id {agent_obj.id} due to missing name, description, or did.")

    except SQLAlchemyError as e:
        logging.error(f"Database error while fetching agents: {e}", exc_info=True)
        raise # Re-raise the exception to stop the script
    except Exception as e:
        logging.error(f"An unexpected error occurred fetching agents: {e}", exc_info=True)
        raise
    finally:
        db.close() # Ensure the session is closed
        logging.info("Database session closed.")

    return agents_data

# --- Main Script Logic ---
try:
    agents = get_agents_from_db()
except Exception:
    # Error already logged in get_agents_from_db, exit script
    sys.exit(1)


if not agents:
    logging.error("No agent data fetched from the database. Cannot build embeddings.")
    sys.exit(1)

# --- Prepare text data for embedding ---
logging.info("Preparing text data for embedding...")
texts = []
# Now 'agents' is already the list of dictionaries we need
for a in agents:
    # Text combination logic remains the same
    name = a.get("name", "")
    desc = a.get("description", "")
    combined = f"{name} {desc}".strip()
    texts.append(combined)

if not texts:
    logging.error("No text data generated from fetched agents.")
    sys.exit(1)

logging.info(f"Prepared text data for {len(texts)} agents.")

# --- Load Model and Generate Embeddings ---
logging.info("Loading Sentence Transformer model...")
try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    logging.error(f"Error loading Sentence Transformer model: {e}", exc_info=True)
    sys.exit(1)

logging.info("Generating embeddings...")
embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

# --- Normalize and Build Faiss Index ---
logging.info("Normalizing embeddings...")
faiss.normalize_L2(embeddings)
dim = embeddings.shape[1]
logging.info(f"Embeddings generated with dimension: {dim}")

logging.info("Building Faiss index (IndexFlatIP)...")
index = faiss.IndexFlatIP(dim)
index.add(embeddings)
logging.info(f"Added {index.ntotal} vectors to the Faiss index.")

# --- Save the model files ---
output_dir = "search_model" # Keep saving to search_model in project root
logging.info(f"Saving model files to '{output_dir}/'...")
os.makedirs(output_dir, exist_ok=True)

embeddings_path = os.path.join(output_dir, "embeddings.npy")
index_path = os.path.join(output_dir, "index.faiss")
agents_output_path = os.path.join(output_dir, "agents.json")

try:
    np.save(embeddings_path, embeddings)
    logging.info(f"Saved embeddings to '{embeddings_path}'")

    faiss.write_index(index, index_path)
    logging.info(f"Saved Faiss index to '{index_path}'")

    # Save the list of agent dictionaries fetched from DB
    with open(agents_output_path, "w", encoding="utf-8") as f:
        json.dump(agents, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved agent metadata (from DB) to '{agents_output_path}'")

except Exception as e:
    logging.error(f"Error saving model files: {e}", exc_info=True)
    sys.exit(1)

logging.info("\nBuild process using database data completed successfully.")