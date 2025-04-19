# MasumiRanker

**MasumiRanker** is a decentralized AI Agent discovery and rating platform built for the [Masumi Network](https://github.com/masumiprotocol).  
It allows users to explore AI agents, submit reviews and ratings, and view category-based rankings in a transparent and verifiable manner.

---

## 🛠 Project Overview

**Hackathon Duration:** 24 hours  
**Team Members:**  
- **Frontend:** Anastasia He (React)
- **Backend:** Thomas Wang (Node.js / Python)
- **ML / Data & Integration:** Claire Wen (PyTorch)

---

## 🔍 Features

### Agent Discovery
- Browse all available agents by name, category, or ID
- Filter by category
- Sort by average rating or popularity

### Agent Detail Page
- View full agent metadata (name, description, DID, external link)
- Submit new ratings (1–5 stars + optional comment)
- Display all ratings and comments with timestamp and hash

### Ranking System
- View top-rated agents in each category
- Sortable by average score or number of reviews

### Audit-Ready Reviews
- All ratings are timestamped and cryptographically hashed (`SHA-256`)
- Each hash ensures ratings cannot be tampered with
- Prepared for on-chain logging in future iterations

---

## 📦 API Specification

Full API documentation is available in [`document/api_spec.md`](document/api_spec.md).

Key endpoints include:

- `GET /agents`: List agents
- `GET /agents/:id`: Agent details
- `POST /ratings`: Submit rating
- `GET /ratings/:agent_id`: All ratings for a specific agent
- `GET /rankings`: Top agents by category

---

## 🗃 Simulated Data Model

Since Masumi APIs are currently limited, we use mock data:

- `agents.json`: List of mock agents with ID, name, category, and metadata
- `ratings.json`: Ratings data with hashed audit trail

---

## 🔒 Data Integrity & Trust

All user-submitted ratings include:

- `timestamp`: Recorded in UTC, ISO 8601 format
- `hash`: SHA-256 hash of `{agent_id + user_id + score + comment + timestamp}`

This ensures verifiability and prepares the system for immutable on-chain logging.

---

## ⚙️ Technologies

- **Frontend:** React.js
- **Backend:** Node.js / Express or Python Flask
- **Mock DB:** JSON file-based simulation
- **Security:** Hashing (crypto / hashlib)
- **ML (Optional):** Sentiment scoring, keyword extraction

---

## 📁 Folder Structure

```
MasumiRanker/
├── document/               # Specifications & design documents
│   ├── api_spec.md
│   └── project_spec.md
├── backend/                # Server-side logic
├── frontend/               # React app
├── mock_data/              # Simulated data (JSON files)
├── scripts/                # Helper scripts (optional)
└── README.md
```

---

## 📄 License

This project is developed under the MIT License for hackathon/demo purposes only.

---

## 🙌 Contribution

Pull requests and forks are welcome for future development. For major changes, please open an issue first.

---
