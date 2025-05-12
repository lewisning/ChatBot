import os
import json
import numpy as np
import faiss
import openai
from dotenv import load_dotenv

"""
Individually test Vector search function
"""

load_dotenv()

# Azure OpenAI Configuration
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

# Load FAISS and metadata
INDEX_PATH = "rag/vector_store.faiss"
META_PATH = "rag/metadata.json"

index = faiss.read_index(INDEX_PATH)

with open(META_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

print(f"[✔] Loading FAISS, {index.ntotal} Records loaded.")

# Embedding user input
def embed_query(query):
    response = openai.Embedding.create(
        input=[query],
        engine=DEPLOYMENT
    )
    return np.array(response["data"][0]["embedding"], dtype="float32")

# Vector searching
def search_similar_chunks(query, top_k=10, distance_threshold=1.2):
    query_vec = embed_query(query)
    D, I = index.search(np.array([query_vec]), top_k)

    results = []
    for dist, idx in zip(D[0], I[0]):
        if idx < len(metadata) and dist < distance_threshold:
            results.append(metadata[idx])
    return results

if __name__ == "__main__":
    # Development testing
    user_input = input("Please enter your question：")
    results = search_similar_chunks(user_input)

    print(f"\n[Top {len(results)} Similar Chunks]:\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] Title: {r['title']}")
        print(f"URL: {r['url']}")
        print(f"Sample display: {r['text'][:200]}...\n")
