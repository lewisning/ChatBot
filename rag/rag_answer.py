import os
import json
import openai
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

INDEX_PATH = "rag/faiss_index.index"
META_PATH = "rag/faiss_metadata.json"

index = faiss.read_index(INDEX_PATH)
with open(META_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

def embed_query(query):
    response = openai.Embedding.create(
        input=[query],
        engine=DEPLOYMENT_EMBED
    )
    return np.array(response["data"][0]["embedding"], dtype="float32")


def search_context(query, top_k=5, distance_threshold=1.5):
    query_vec = embed_query(query)
    D, I = index.search(np.array([query_vec]), top_k)

    contexts = []
    references = []

    for dist, i in zip(D[0], I[0]):
        if i < len(metadata) and dist < distance_threshold:
            item = metadata[i]
            meta = item.get("metadata", {})
            content = item.get("content", "")

            contexts.append(content)
            references.append({
                "title": meta.get("product_name"),
                "brand": meta.get("brand"),
                "category": meta.get("category"),
                "chunk_type": meta.get("chunk_type"),
                "url": meta.get("url"),
                "number": len(references) + 1
            })

    return "\n---\n".join(contexts), references


def ask_with_context(question, chatbot_name):
    context, references = search_context(question)

    sys_prompt = f"""
                    Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question no matter the question contains keywords such as "nestle".
                    
                    Do not rely on your own knowledge or assumptions.
                    If the user asks for your name, respond with: "My name is {chatbot_name}, I'm your personal MadeWithNestle assistant."
                    Be concise, factual, and in English. Do not say 'based on the context'.
                    Only use content that is clearly relevant to the question.
                    Ignore irrelevant products or content even if they are nearby in the context.
    
                    Please format your answer based on the type:
                    1. If the answer contains **product recommendations**, show each product as a markdown hyperlink like [**Product Name**](url of each product name from the context provided).
                    2. If the answer contains **factual or informational content**, insert markdown hyperlinks directly inside the text, and add a citation number in format of [1], [2] ... etc. after each link **inside the text**.
                    Do not include a "References" section at the end of the message.
                    Use markdown formatting for links and bulleted lists where appropriate.
                  """

    user_prompt = f"""
                    Context:
                    {context}
                    
                    Question:
                    {question}
                  """

    response = openai.ChatCompletion.create(
        engine=DEPLOYMENT_GPT,
        messages=[{"role": "system", "content": sys_prompt},
                  {"role": "user", "content": user_prompt}],
        temperature=0,
        max_tokens=300
    )

    # Format response with references
    base_answer = response["choices"][0]["message"]["content"].strip()

    # Reduce duplicate references
    used_titles = set()
    for ref in references:
        product = ref["title"].strip()
        url = ref["url"]
        number = ref["number"]

        if product in base_answer and product not in used_titles:
            base_answer = base_answer.replace(
                product,
                f"[{product}]({url})[{number}]"
            )
            used_titles.add(product)

    return {
        "answer": base_answer,
        "references": references
    }
