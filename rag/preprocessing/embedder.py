import json
import os
from dotenv import load_dotenv
import openai
import faiss
import numpy as np
from tqdm import tqdm

# ========== Configure OpenAI Key ==========
load_dotenv()
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

# ========== Load Chunk data ==========
with open("rag/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

# ========== Extract text and metadata ==========
texts = [chunk["content"] for chunk in chunks]

# ========== Generate embeddings ==========
print("Generating embeddings...")

embeddings = []
batch_size = 50
for i in tqdm(range(0, len(texts), batch_size)):
    batch = texts[i:i+batch_size]
    response = openai.Embedding.create(
        deployment_id=DEPLOYMENT,
        input=batch
    )
    batch_embeddings = [item["embedding"] for item in response["data"]]
    embeddings.extend(batch_embeddings)

embeddings = np.array(embeddings).astype("float32")  # FAISS 需要 float32

# ========== Construct FAISS index ==========
dim = len(embeddings[0])
index = faiss.IndexFlatL2(dim)
index.add(embeddings)

# ========== Save FAISS index and related metadata ==========
faiss.write_index(index, "rag/faiss_index.index")
with open("rag/faiss_metadata.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"Done! Embedded {len(chunks)} chunks.")
print("Saved: faiss_index.index and faiss_metadata.json")
