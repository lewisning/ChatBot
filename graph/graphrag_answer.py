from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import openai


load_dotenv()

# Azure OpenAI Configuration
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT_GPT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
DEPLOYMENT_EMBED = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")


# === Query from Neo4j with GraphRAG ===
def query_brand_products(brand_name):
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test1234"))

    with driver.session() as session:
        result = session.run("""
            MATCH (b:Brand {name: $brand})-[:OWNS]->(p:Product)
            RETURN p.name AS name, p.url AS url, p.description AS description
        """, brand=brand_name)

        lines = [f"Brand: {brand_name}\n"]
        for record in result:
            lines.append(f"Product: {record['name']}\nURL: {record['url']}\nDescription: {record['description']}\n")
        return "\n".join(lines)


# === Context Construction ===
def build_prompt(context, question, chatbot_name):
    return f"""
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
            
            Context:{context}
            
            Question:{question}
            Answer:
            """


# === Main Function ===
def answer_question(brand_name, question):
    context = query_brand_products(brand_name)
    prompt = build_prompt(context, question)

    response = openai.ChatCompletion.create(
        model=DEPLOYMENT_GPT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response['choices'][0]['message']['content'].strip()
