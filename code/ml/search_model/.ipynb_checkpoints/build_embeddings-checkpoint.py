import json
import numpy as np
import faiss
import os
from sentence_transformers import SentenceTransformer

with open("masumi_entries.json", "r", encoding="utf-8") as f:
    data = json.load(f)

agents = data["data"]["entries"]

texts = []
for a in agents:
    name = a["name"]
    desc = a["description"]
    combined = f"{name} {desc}"
    texts.append(combined)

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(texts, convert_to_numpy=True)
faiss.normalize_L2(embeddings)
dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)
index.add(embeddings)

os.makedirs("search_model", exist_ok=True)
np.save("search_model/embeddings.npy", embeddings)
faiss.write_index(index, "search_model/index.faiss")
with open("search_model/agents.json", "w", encoding="utf-8") as f:
    json.dump(agents, f, ensure_ascii=False, indent=2)

print("Model files saved to 'search_model/'")
