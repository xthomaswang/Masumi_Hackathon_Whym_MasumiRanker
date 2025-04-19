Okay, here is a revised, more detailed and formal `README.md` based on the actual functionalities and technologies implemented in your project. It incorporates the features like semantic search, the two-database system for recommendations, and the correct technology stack.

---

# MasumiRanker: AI Agent Discovery, Rating, and Search Platform

**MasumiRanker** is a comprehensive platform developed during the Masumi 真墨 Hackathondesigned for the discovery, evaluation, and semantic searching of AI Agents, envisioned for integration with the [Masumi Network](https://github.com/masumiprotocol). It provides a robust backend API enabling users to browse agents, submit detailed ratings, search for agents based on natural language descriptions, and interact with a recommendation system.

---

## Features

This platform implements the following core features:

1.  **Agent Discovery & Display:**
    * **List Agents (`GET /api/agents`):** Retrieves a paginated list of all registered AI agents, sorted by average user rating (descending) by default.
    * **Agent Details (`GET /api/agents/{agent_id}`):** Fetches comprehensive metadata for a specific agent using its internal database ID, including name, description, category, DID, URL, pricing, aggregated rating, and image URL.
    * **Static Image Serving:** Serves agent-specific images stored locally via a dedicated `/images/...` path.

2.  **User Ratings & Reviews:**
    * **Submit Ratings (`POST /api/ratings`):** Allows users to submit a numerical score (1-5) and an optional textual comment for any agent.
    * **Score Aggregation:** Automatically recalculates and updates the agent's average score and total number of ratings in the main database upon receiving a new valid rating.
    * **Retrieve Ratings (`GET /api/ratings/by-agent`, `GET /api/ratings/by-did`):** Provides endpoints to fetch all submitted ratings for a specific agent, identified either by its internal ID or its Decentralized Identifier (DID), with pagination support.
    * **Data Integrity:** Each submitted rating includes a UTC timestamp and a SHA-256 hash (`hash = SHA-256(agent_id + user_id + score + comment + timestamp)`) to ensure verifiability and prepare for potential future on-chain logging.

3.  **Semantic Search (`POST /api/search`):**
    * **Natural Language Queries:** Enables users to search for agents using descriptive text queries instead of just keywords.
    * **AI-Powered Matching:** Utilizes Sentence Transformers (`all-MiniLM-L6-v2`) to generate vector embeddings for agent descriptions/names and incoming queries. Employs Faiss (`IndexFlatIP`) for efficient high-dimensional similarity search based on these embeddings.
    * **Ranked Results:** Returns a list of the top `k` agents most semantically relevant to the user's query, including agent details (ID, DID, name, description) and the similarity score.
    * **Offline Indexing:** Requires a separate build step (`build_embeddings.py`) to pre-compute embeddings and the Faiss index from agent data stored in the main database.

4.  **Recommendation System (Event Logging & Retrieval):**
    * **Dual Database Approach:** Uses a separate SQLite database (`recommend.db`) for recommendation-related data to potentially allow independent management.
    * **Log Recommendation Events (`POST /api/recommendations`):** Records an event when a specific agent (identified by DID) is recommended. Stores the agent's DID and a timestamp in the `recommendations` table within `recommend.db`. It first verifies the agent DID exists in the main database.
    * **Retrieve Recommended Agent DIDs (`GET /api/recommendations`):** Queries the `recommendations` event log table in `recommend.db` and returns a list of unique DIDs that have been previously logged via the POST endpoint. *(Note: This currently retrieves from the event log, not a manually curated/ranked list)*.

5.  **Database & Infrastructure:**
    * **Database Initialization:** Automatically creates necessary tables in both the main database (`masumi.db`) and the recommendation database (`recommend.db`) on application startup if they don't already exist.
    * **Health Check:** Provides a root endpoint (`GET /`) for basic service health verification.
    * **API Documentation:** Automatically generates interactive API documentation (Swagger UI) available at `/docs` and the OpenAPI schema at `/openapi.json`.
    * **(Disabled) Masumi Registry Sync:** Contains infrastructure (code and database models) for syncing with an external Masumi Registry, but this functionality is currently disabled in the application configuration.

---

## Technology Stack

* **Backend Framework:** Python 3.10+ with FastAPI
* **Database:** SQLite
* **ORM:** SQLAlchemy
* **Data Validation:** Pydantic
* **API Server:** Uvicorn (ASGI Server)
* **Semantic Search:**
    * Sentence Transformers (`all-MiniLM-L6-v2`)
    * Faiss (Facebook AI Similarity Search) - CPU version
    * Numpy
* **Dependencies & Environment:** Conda (for environment management), python-dotenv (for potential environment variable loading)
* **Frontend:** React.js (Served separately, interacts with this backend API)

---

## API Endpoints

All functional endpoints are prefixed with `/api`. Key endpoints include:

* `GET /agents`: Retrieves a paginated list of agents.
* `GET /agents/{agent_id}`: Retrieves details for a specific agent.
* `POST /ratings`: Submits a new rating for an agent.
* `GET /ratings/by-agent?agent_id={agent_id}`: Gets ratings for an agent by internal ID.
* `GET /ratings/by-did?did={did}`: Gets ratings for an agent by DID.
* `POST /search`: Performs semantic search based on a JSON body: `{"query": "...", "top_k": ...}`.
* `POST /recommendations`: Logs a recommendation event for a given DID in the JSON body: `{"did": "..."}`.
* `GET /recommendations`: Retrieves a list of unique DIDs from the recommendation event log: `{"dids": [...]}`.

Interactive documentation is available at `/docs` when the server is running.

---

## Database Schema Overview

Two SQLite databases are used:

1.  **Main Database (`masumi.db`):** Located at `code/backend/database/masumi.db`
    * **`agents` table (Model: `Agent`):** Stores core agent information, including aggregated ratings.
    * **`ratings` table (Model: `Rating`):** Stores individual user ratings and comments.
    * **`registry` table (Model: `RegistryEntry`):** Intended for raw Masumi data (currently unused due to disabled sync).
2.  **Recommendation Database (`recommend.db`):** Located at `code/backend/database/recommend.db`
    * **`recommendations` table (Model: `Recommendation`):** Logs recommendation events (DID + Timestamp). Populated by `POST /api/recommendations`.
    * **`recommended` table (Model: `RecommendedAgent`):** Designed to store a manually curated list of ranked agents (DID, Rank, Note). Populated manually via SQLite tools; read by an earlier (now overwritten) version of `GET /api/recommendations`. *(Note: The current GET endpoint reads the `recommendations` table instead)*.

Database paths are configured using absolute paths within `code/backend/database/database.py` and `code/backend/database/recommend_db.py`. Tables are created automatically on application startup if they do not exist.

---

## Setup and Running

### Prerequisites

* Python 3.10 or later
* Conda (recommended for environment management)
* Access to a command line/terminal

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/xthomaswang/Masumi_Hackathon_Whym_MasumiRanker
    cd Masumi_hackathon_Whym_MasumiRanker
    ```
2.  **Create/Activate Conda Environment:**
    ```bash
    # conda create --name ranker python=3.10 # If creating for the first time
    conda activate ranker
    ```
3.  **Install Dependencies:** Ensure the `requirements.txt` file is in the project root.
    ```bash
    pip install -r requirements.txt
    ```

### Database Setup

1.  **Main Database (`masumi.db`):** This database needs to be populated with agent data *before* running the build script. The application startup (`./run.sh`) will create the file and tables if they don't exist, but it will be empty initially. You may need a separate script or manual process to populate the `agents` table initially.
2.  **Recommendation Database (`recommend.db`):** The application startup (`./run.sh`) will create this file and the `recommendations` / `recommended` tables if they don't exist.
    * To get results from `GET /api/recommendations`, you currently need data in the `recommendations` table (added via `POST /api/recommendations`).
    * *(If you revert the GET logic): To get results from a curated list, you would need to manually populate the `recommended` table using a SQLite browser tool.*

### Build Search Index (Mandatory for Search Functionality)

1.  Ensure the main database (`masumi.db`) contains agent data.
2.  Run the build script **from the project root directory**:
    ```bash
    # Ensure 'ranker' environment is active
    python -m code.ml.search_model.build_embeddings
    ```
3.  This will create the `search_model/` directory in the project root containing `embeddings.npy`, `index.faiss`, and `agents.json`. These files are required for the search API to function. Rerun this script if the agent data in `masumi.db` changes significantly.

### Configuration

* Database paths are currently configured using absolute paths derived within the respective `database.py` and `recommend_db.py` files.
* An `.env` file in the project root can be used for other potential configurations if needed in the future (e.g., API keys, external service URLs).

### Running the Application

1.  Make sure you are in the project root directory (`Masumi_hackathon_Whym_MasumiRanker`).
2.  Ensure the Conda environment is active (`conda activate ranker`).
3.  Run the launch script:
    ```bash
    ./run.sh
    ```
4.  The API server should start (default: `http://0.0.0.0:8000`). Access interactive documentation at `http://localhost:8000/docs`.

---

## Folder Structure

```
Masumi_hackathon_Whym_MasumiRanker/
├── code/
│   ├── backend/
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── database.py         # Main DB setup (masumi.db)
│   │   │   ├── models.py           # SQLAlchemy models (for both DBs)
│   │   │   ├── recommend_db.py     # Recommendation DB setup (recommend.db)
│   │   │   └── masumi.db           # Main SQLite DB file
│   │   │   └── recommend.db        # Recommendation SQLite DB file
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── route.py            # API endpoint definitions
│   │   ├── __init__.py
│   │   └── main.py                 # FastAPI app entry point, middleware, startup
│   ├── ml/
│   │   └── search_model/
│   │       ├── __init__.py
│   │       └── build_embeddings.py # Script to build search index
│   └── __init__.py
├── dataset/
│   └── image/                      # Static agent images
├── document/                       # Documentation files
│   └── api_spec.md                 # (Example placeholder)
├── search_model/                   # Output of build_embeddings.py
│   ├── agents.json
│   ├── embeddings.npy
│   └── index.faiss
├── .env                            # Environment variables (if used)
├── .gitignore
├── README.md                       # This file
├── requirements.txt                # Python dependencies
└── run.sh                          # Script to run the backend server
```

---

## `requirements.txt`

```txt
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary # Or appropriate DB driver if you switched from SQLite
pydantic
python-dotenv
apscheduler
requests
# --- Search Dependencies ---
faiss-cpu # Or faiss-gpu
sentence-transformers
numpy
```
*(Note: Ensure this list accurately reflects all installed packages, especially the database driver used)*

---

## License

This project is developed under the MIT License. See the `LICENSE` file for details.

---

## Contributing

Contributions, issues, and feature requests are welcome. For major changes, please open an issue first to discuss what you would like to change.