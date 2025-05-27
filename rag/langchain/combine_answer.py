from rest_framework.response import Response
from langchain.chat_models import AzureChatOpenAI
from langchain.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain, MultiRetrievalQAChain
import os
from dotenv import load_dotenv

# Initialize Azure OpenAI
load_dotenv()
llm = AzureChatOpenAI(
    openai_api_type="azure",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    temperature=0
)

# Neo4j Graph Configuration
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# GraphCypherQAChain Configuration with custom prompt
graph_chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True,
    return_intermediate_steps=True,
    cypher_prompt_template="""
                            You are a Cypher expert. Only generate READ-ONLY Cypher queries.
                        
                            Schema:
                            (:Brand)-[:OWNS]->(:Product {name, specification, category, url, status})
                            (:Product)-[:HAS_NUTRITION]->(:Nutrition {unit, daily_percent, name, value})
                            (:Product)-[:HAS_FEATURE]->(:Feature {name})
                            (:Product)-[:HAS_INGREDIENT]->(:Ingredient {name})
                        
                            IMPORTANT INSTRUCTIONS:
                            - All nutrition names are capitalized. For example: 'Calories', 'Fat', 'Protein', 'Sodium'.
                            - Always use lowercase for all nutrition field values in MATCH and WHERE clauses. For example:
                              `MATCH (n:Nutrition {name: "calories"})`
                              Do NOT use: `name: "calories"` (lowercase for nutrition names).
                            - If the answer contains **product recommendations**, show each product as a markdown hyperlink like [**Product Name**](url of each product name from the context provided).
                        
                            Query examples:
                            Example 1:
                            MATCH (p:Product)-[:HAS_NUTRITION]->(n:Nutrition {name: "calories"})
                            RETURN p.name, n.value
                        
                            Example 2:
                            MATCH (p:Product)-[:HAS_NUTRITION]->(n:Nutrition)
                            WHERE n.name = "protein"
                            RETURN p.name, n.value
                        
                            You can use `CALL db.schema.visualization()` to inspect schema.
                        
                            DO NOT use CREATE, DELETE, or MERGE. Only use READ-ONLY queries.
                            
                            Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question no matter the question contains keywords such as "nestle".
                    
                            Do not rely on your own knowledge or assumptions.
                            If the user asks for your name, respond with: "My name is {chatbot_name}, I'm your personal MadeWithNestle assistant."
                            """
)

def grag_view(question):
    if not question:
        return Response({"error": "Missing question."}, status=400)

    # Query with GraphRAG
    try:
        answer = graph_chain.invoke(question)
        return Response({"answer": answer["result"]}, status=200)
    except Exception as e:
        answer = ""
        print("[ERROR]", e)
        return Response({"error": str(e)}, status=500)


    # Step 1: Query Neo4j Graph
    # try:
    #     answer = graph_chain.invoke(question)
    #     if answer:
    #         answer = answer["result"]
    #     else:
    #         answer = ""
    # except Exception as e:
    #     answer = ""
    #
    # if answer == "":
    #     # Step 2: Query LangChain RAG
    #     try:
    #         answer = query_with_langchain_rag(question, name)
    #         # references = result["sources"]
    #     except Exception as e:
    #         context = ""
    #
    # # Step 3: Construct the prompt for GPT
    # # prompt = f"""
    # #         You are a helpful assistant answering user questions about Nestlé products.
    # #
    # #         Answer the user's question using both sources if possible. If only one is available, use it. Be factual and concise.
    # #
    # #         Question: {question}
    # #
    # #         Answer:
    # #         """
    # #
    # # # Step 4: Answer using the LLM
    # # final_response = llm.predict(prompt)
    #
    # return Response({
    #     "answer": answer,
    #     "references": []
    # })