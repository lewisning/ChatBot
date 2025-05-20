from rest_framework.decorators import api_view
from rest_framework.response import Response
from langchain.chat_models import AzureChatOpenAI
from langchain.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain, MultiRetrievalQAChain
# from rag.preprocessing.query_with_rag import query_with_rag
from rag.langchain.rag_answer import query_with_langchain_rag
from typing import List
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever
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
    url="bolt://localhost:7687",
    username="neo4j",
    password="test1234"
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
                            - Always use capitalized nutrition field values in MATCH and WHERE clauses. For example:
                              `MATCH (n:Nutrition {name: "Calories"})`
                              Do NOT use: `name: "calories"` (lowercase)
                            - If unsure, always assume capitalized form for nutrition names.
                            - If the answer contains **product recommendations**, show each product as a markdown hyperlink like [**Product Name**](url of each product name from the context provided).
                        
                            Query examples:
                            Example 1:
                            MATCH (p:Product)-[:HAS_NUTRITION]->(n:Nutrition {name: "Calories"})
                            RETURN p.name, n.value
                        
                            Example 2:
                            MATCH (p:Product)-[:HAS_NUTRITION]->(n:Nutrition)
                            WHERE n.name = "Protein"
                            RETURN p.name, n.value
                        
                            You can use `CALL db.schema.visualization()` to inspect schema.
                        
                            DO NOT use CREATE, DELETE, or MERGE. Only use READ-ONLY queries.
                            
                            Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question no matter the question contains keywords such as "nestle".
                    
                            Do not rely on your own knowledge or assumptions.
                            If the user asks for your name, respond with: "My name is {chatbot_name}, I'm your personal MadeWithNestle assistant."
                            """
)


@api_view(["POST"])
def grag_view(request):
    question = request.data.get("question", "")
    name = request.data.get("name")
    if not question:
        return Response({"error": "Missing question."}, status=400)


    # # Query combined RAG and GraphRAG
    # try:
    #     graph_answer = graph_chain.invoke(question)
    #     print(graph_answer)
    # except Exception as e:
    #     graph_answer = ""
    #     print("[ERROR]", e)
    #     return Response({"error": str(e)}, status=500)
    #
    # vector_retriever = query_with_langchain_rag(question, name)
    #
    # multi_chain = MultiRetrievalQAChain.from_retrievers(
    #     llm=llm,
    #     retriever_infos=[
    #         {
    #             "name": "graph",
    #             "retriever": graph_answer.get("context", {}),
    #             "description": "Structured product data like brand, nutrition, and ingredients from Neo4j knowledge graph."
    #         },
    #         {
    #             "name": "vector",
    #             "retriever": vector_retriever,
    #             "description": "Unstructured text content such as packaging, product descriptions, and features."
    #         }
    #     ],
    #     verbose=True
    # )
    #
    # # Run the multichain query
    # try:
    #     answer = multi_chain.run(question)
    # except Exception as e:
    #     print("[ERROR]", e)
    #     return Response({"error": str(e)}, status=500)
    #
    # return Response({
    #     "answer": answer
    # })


    # Step 1: Query Neo4j Graph
    try:
        answer = graph_chain.invoke(question)
        answer = answer["result"]
    except Exception as e:
        answer = ""

    if not answer:
        # Step 2: Query LangChain RAG
        try:
            answer = query_with_langchain_rag(question, name)
            # references = result["sources"]
        except Exception as e:
            context = ""

    # Step 3: Construct the prompt for GPT
    # prompt = f"""
    #         You are a helpful assistant answering user questions about Nestlé products.
    #
    #         Answer the user's question using both sources if possible. If only one is available, use it. Be factual and concise.
    #
    #         Question: {question}
    #
    #         Answer:
    #         """
    #
    # # Step 4: Answer using the LLM
    # final_response = llm.predict(prompt)

    return Response({
        "answer": answer,
        "references": []
    })