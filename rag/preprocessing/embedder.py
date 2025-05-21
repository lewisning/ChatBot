import json
import os
from dotenv import load_dotenv

from langchain_openai import AzureOpenAIEmbeddings
from langchain.vectorstores import FAISS

# ========== Configure Azure OpenAI ==========
load_dotenv()
embedding_model = AzureOpenAIEmbeddings(
    deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
    openai_api_type="azure",
    chunk_size=16
)

# ========== Load chunk data ==========
with open("rag/chunks.json", "r", encoding="utf-8") as f:
    raw_chunks = json.load(f)

texts = []
metadatas = []
for i, chunk in enumerate(raw_chunks):
    chunk_id = f"chunk_{i}"
    chunk["chunk_id"] = chunk_id
    texts.append(chunk["content"])
    metadatas.append(chunk["metadata"])

# ========== Generate and Save LangChain FAISS ==========
print("Embedding and building FAISS index...")

faiss_index = FAISS.from_texts(texts=texts, embedding=embedding_model, metadatas=metadatas)
faiss_index.save_local("rag/faiss_index")

print(f"Embedded {len(texts)} chunks.")
print("Saved to rag/faiss_index/")
