from langchain_community.graphs import Neo4jGraph
from langchain_openai import AzureChatOpenAI
from langchain.chains import GraphCypherQAChain
import openai
import os
from dotenv import load_dotenv

# 1. Initialize Azure OpenAI
load_dotenv()
llm = AzureChatOpenAI(
    openai_api_type="azure",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    temperature=0
)

# 2. Initialize Neo4j Graph
graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="test1234"
)

schema = """
        CALL db.schema.visualization()

        Do not use DELETE, CREATE, or MERGE outside querying. Only read data.
        """

# 3. Initialize GraphCypherQAChain
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,  # 打印生成的 Cypher
    allow_dangerous_requests=True,
    cypher_prompt_template=f"""
                            You are a Cypher expert. Only generate READ-ONLY Cypher queries.
                            Schema:
                            {schema}
                            """
)

# 4. Ask a question
question = "How many products do you have in total?"
result = chain.invoke(question)
print(result)
