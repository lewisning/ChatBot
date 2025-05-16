import faiss

FAISS_PATH = "rag/faiss_index.index"

index = faiss.read_index(FAISS_PATH)
print(f"[✔] FAISS index loaded.")
print(f"Vector Dimension: {index.d}（Should be 1536）")
print(f"Number of Vectors: {index.ntotal}")

import json

with open("rag/faiss_metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

print(f"[✔] Metadata Load Successful, {len(metadata)} records loaded.")
print("Example:")
print(json.dumps(metadata[0], indent=2, ensure_ascii=False))
assert index.ntotal == len(metadata), "ATTENTION: FAISS index and metadata mismatch."
