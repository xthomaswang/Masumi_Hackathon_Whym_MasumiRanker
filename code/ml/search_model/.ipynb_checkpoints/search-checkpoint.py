import json
import numpy as np
import faiss
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer

with open("search_model/agents.json", "r", encoding="utf-8") as f:
    agents = json.load(f)

embeddings = np.load("search_model/embeddings.npy")
index = faiss.read_index("search_model/index.faiss")
model = SentenceTransformer("all-MiniLM-L6-v2")

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class QueryResponse(BaseModel):
    ids: List[str]

@app.post("/search", response_model=QueryResponse)
def search_agents(request: QueryRequest):
    q_emb = model.encode([request.query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)
    scores, ids = index.search(q_emb, request.top_k)
    result_ids = [agents[idx]["did"] for idx in ids[0]]
    return {"ids": result_ids}
