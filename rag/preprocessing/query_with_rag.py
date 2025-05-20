import faiss
import json
import numpy as np
import openai
import os
from dotenv import load_dotenv

# ========== Configure OpenAI ==========
load_dotenv()
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
LLM_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# ========== Load FAISS index and metadata ==========
index = faiss.read_index("rag/faiss_index.index")

with open("rag/metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# ========== Core Function ==========
def query_with_rag(question, chatbot_name, top_k=60, distance_threshold=1.5):
    # Step 1: Embed the query
    response = openai.Embedding.create(
        deployment_id=DEPLOYMENT,
        input=[question]
    )
    query_vec = np.array(response["data"][0]["embedding"]).astype("float32")

    # Step 2: FAISS similarity search
    D, I = index.search(np.array([query_vec]), top_k)

    # Step 3: Filter by distance threshold and collect context
    contexts = []
    sources = []
    for dist, i in zip(D[0], I[0]):
        if i < len(metadata) and dist < distance_threshold:
            meta = metadata[i]
            context_text = meta.get("content", "")
            contexts.append(context_text)

            sources.append({
                "brand": meta.get("metadata", {}).get("brand"),
                "product_name": meta.get("metadata", {}).get("product_name", ""),
                "brand_url": meta.get("metadata", {}).get("brand_url", ""),
                # "field": meta.get("metadata", {}).get("field"),
                "url": meta.get("metadata", {}).get("product_url", ""),
                # "distance": round(float(dist), 4)
            })

    full_context = "\n---\n".join(contexts)

    # Step 4: Call LLM (Optional: you can skip this step and just return context if needed)
    sys_prompt = f"""
                        Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question no matter the question contains keywords such as "nestle".

                        Do not rely on your own knowledge or assumptions.
                        If the user asks for your name, respond with: "My name is {chatbot_name}, I'm your personal MadeWithNestle assistant."
                        Be concise, factual, and in English. Do not say 'based on the context'.
                        Only use content that is clearly relevant to the question.
                        Ignore irrelevant products or content even if they are nearby in the context.

                        Please format your answer based on the type:
                        1. If the answer contains **product (brand) recommendations**, show each product as a markdown hyperlink like [**Product (Brand) Name**](url of each product from the context provided) and add "you can visit following links:" before you provide the link.
                        2. If the answer contains **factual or informational content**, insert markdown hyperlinks directly inside the text, and add a citation number in format of [1], [2] ... etc. after each link **inside the text**.
                        Do not include a "References" section at the end of the message.
                        Use markdown formatting for links and bulleted lists where appropriate.

                      """

    user_prompt = f"""
                        Context:
                        {full_context}
                        Question:
                        {question}
                      """

    completion = openai.ChatCompletion.create(
        deployment_id=LLM_DEPLOYMENT,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=300
    )

    answer = completion["choices"][0]["message"]["content"]

    # Reduce duplicate references
    used_titles = set()
    url_counter = {}
    counter = 1
    reference = []
    # for ref in sources:
    #     product = ref.get("product_name", "")
    #     brand = ref.get("brand", "")
    #     url = ref.get("url")
    #
    #     if product in answer and product not in used_titles:
    #         answer = answer.replace(
    #             product,
    #             f"[**{product}**]({url})[{counter}]"
    #         )
    #         reference.append({"url": url, "number": counter})
    #         used_titles.add(product)
    #         counter += 1
    #     if brand in answer and brand not in used_titles:
    #         answer = answer.replace(
    #             brand,
    #             f"[**{brand}**]({url})[{counter}]"
    #         )
    #         reference.append({"url": url, "number": counter})
    #         used_titles.add(product)
    #         counter += 1

    return {
        # "question": query,
        "answer": full_context,
        # "context_used": contexts,
        "reference": reference
    }

# def query_with_rag(question, top_k=5, distance_threshold=0.7):
#     response = openai.Embedding.create(
#                 deployment_id=DEPLOYMENT,
#                 input=[question]
#             )
#     query_vec = np.array(response["data"][0]["embedding"]).astype("float32")
#     D, I = index.search(np.array([query_vec]), top_k)
#
#     contexts = []
#     sources = []
#
#     for dist, i in zip(D[0], I[0]):
#         if i < len(metadata) and dist < distance_threshold:
#             meta = metadata[i]
#             content = meta.get("content", "")
#             contexts.append(content)
#
#             sources.append({
#                 "brand": meta.get("metadata", {}).get("brand"),
#                 "product_name": meta.get("metadata", {}).get("product_name"),
#                 "product_url": meta.get("metadata", {}).get("product_url"),
#                 "brand_url": meta.get("metadata", {}).get("brand_url")
#             })
#
#     context_text = "\n".join(contexts)
#     return context_text, sources


if __name__ == "__main__":
    query = "what brands do you have?"
    result = query_with_rag(query, "s")
    print("\n🧠 Answer:\n", result["answer"])
    print("\n📚 Sources:\n", result["reference"])