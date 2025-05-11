import os
import json
import openai
import faiss
import tiktoken
from dotenv import load_dotenv
import numpy as np


load_dotenv()

# Azure OpenAI Configuration
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

# Data files Path
DATA_FILE = "rag/data.json"
FAISS_INDEX = "rag/vector_store.faiss"
METADATA_FILE = "rag/metadata.json"

# Split data into chunks
def split_text(text, max_tokens=500):
    encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
    tokens = encoding.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i+max_tokens]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

# Generate embedding vectors
def embed_texts(texts):
    response = openai.Embedding.create(
        input=texts,
        engine=DEPLOYMENT
    )
    return [r["embedding"] for r in response["data"]]

def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = []
    metadatas = []

    for entry in data:
        url = entry["url"]
        title = entry["title"]
        base_text = entry["text"]

        # Process text
        chunks = split_text(base_text)
        for i, chunk in enumerate(chunks):
            texts.append(chunk)
            metadatas.append({
                "url": url,
                "title": title,
                "chunk_index": i,
                "text": chunk
            })

    print(f"[+] Ready to embed {len(texts)} chunks.")

    # Generate embedding vectors
    vectors = embed_texts(texts)

    # Create FAISS index
    dim = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors).astype("float32"))

    # Save FAISS index and metadata
    faiss.write_index(index, FAISS_INDEX)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadatas, f, ensure_ascii=False, indent=2)

    print(f"[✔] Embedding successful，saved {len(vectors)} vectors.")

if __name__ == "__main__":
    main()
