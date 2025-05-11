import os
import json
import openai
import time
from openai.error import RateLimitError
import numpy as np
import faiss
from dotenv import load_dotenv

load_dotenv()

# Azure OpenAI Configuration
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT_GPT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
DEPLOYMENT_EMBED = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

# Context loading
INDEX_PATH = "rag/vector_store.faiss"
META_PATH = "rag/metadata.json"

# Loading FAISS index and metadata
index = faiss.read_index(INDEX_PATH)
with open(META_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

def embed_query(query):
    response = openai.Embedding.create(
        input=[query],
        engine=DEPLOYMENT_EMBED
    )
    return np.array(response["data"][0]["embedding"], dtype="float32")

def search_context(query, top_k=5):
    query_vec = embed_query(query)
    D, I = index.search(np.array([query_vec]), top_k)
    contexts = []
    for i in I[0]:
        if i < len(metadata):
            m = metadata[i]
            # Ensure multiple chunks with same product information connect logically
            formatted = f"[{m['title']}] (chunk {m['chunk_index']})\n{m['text']}"
            contexts.append(formatted)
    return "\n---\n".join(contexts)

def ask_with_context(question):
    context = search_context(question)

    prompt = f"""
                Answer the question based only on the following content.
                Be concise, factual, and in English.
                Do not mention the source or say 'based on the context'.
                            
                Context:
                {context}
                
                Question:
                {question}
                
                Answer:
             """

    response = openai.ChatCompletion.create(
        engine=DEPLOYMENT_GPT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300
    )

    return response["choices"][0]["message"]["content"].strip()

if __name__ == "__main__":
    # Development Testing
    while True:
        query = input("Enter your question (or type 'exit' to quit): ").strip()
        if query.lower() == "exit":
            break

        while True:
            try:
                answer = ask_with_context(query)
                print("\n[Answer]:\n", answer)
                break  # Retry gpt prompt since free tier has quota limitation
            except RateLimitError:
                print("\n[!] Rate limit reached. Waiting 60 seconds to retry...")
                for i in range(60, 0, -1):
                    print(f"Retrying in {i} seconds...", end='\r')
                    time.sleep(1)
                print("\n[↻] Retrying...")
