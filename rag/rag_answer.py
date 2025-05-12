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

INDEX_PATH = "rag/vector_store.faiss"
META_PATH = "rag/metadata.json"

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
            meta = metadata[i]
            contexts.append(meta["text"])
            references.append({
                "url": meta["url"],
                "title": meta.get("title"),
                "number": len(references) + 1
            })

    return "\n---\n".join(contexts), references


def ask_with_context(question, chatbot_name):
    context, references = search_context(question)

    prompt = f"""
                You are a helpful assistant named {chatbot_name}, helping users discover Nestlé products.
                Answer the question based only on the following content.
                If the user asks for your name, respond with: "My name is {chatbot_name}, I'm your personal MadeWithNestle assistant."
                Be concise, factual, and in English. Do not say 'based on the context'.
                Only use content that is clearly relevant to the question.
                Ignore irrelevant products or content even if they are nearby in the context.

                Please format your answer based on the type:
                1. If the answer contains **product recommendations**, show each product as a markdown hyperlink like [**Product Name**](https://example.com). Do not include any [1], [2] citations, and do not show a references section.
                2. If the answer contains **factual or informational content**, insert markdown hyperlinks directly inside the text, and add a [1], [2] citation number after each link **inside the text**. Do not include a "References" section at the end of the message.
                Use markdown formatting for links and bulleted lists where appropriate.
                
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
