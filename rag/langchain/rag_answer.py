from langchain.chains.llm import LLMChain
from langchain.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# === Azure OpenAI Configure ===
from dotenv import load_dotenv
import os

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
AZURE_OPENAI_MODEL_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")


def query_with_langchain_rag(question, chatbot_name):
    # 1. Construct the embedding model
    embedding = AzureOpenAIEmbeddings(
        deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
        openai_api_type="azure",
        chunk_size=16
    )

    # 2. Load the FAISS index
    vectorstore = FAISS.load_local("rag/faiss_index", embedding, allow_dangerous_deserialization=True)
    # vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 60})  # Add for MultiRetrievalQAChain
    #
    # return vector_retriever

    # 3. Construct the LLM
    # Define the prompt template
    prompt_template = PromptTemplate(
        input_variables=["context", "question", "chatbot_name"],
        template="""
                    Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question no matter the question contains keywords such as "nestle".

                    Do not rely on your own knowledge or assumptions.
                    If the user asks for your name, respond with: "My name is {chatbot_name}, I'm your personal MadeWithNestle assistant."
                    Be concise, factual, and in English. **Do not say 'based on the context'**.
                    Only use content that is clearly relevant to the question.
                    Ignore irrelevant products or content even if they are nearby in the context.

                    Please format your answer based on the type:
                    1. If the answer contains **product (brand) recommendations**, show each product as a markdown hyperlink like [**Product (Brand) Name**](url of each product from the context provided) and add "you can visit following links:" before you provide the link.
                    2. If the answer contains **factual or informational content**, insert markdown hyperlinks directly inside the text, and add a citation number in format of [1], [2] ... etc. after each link **inside the text**.
                    Do not include a "References" section at the end of the message.
                    Use markdown formatting for links and bulleted lists where appropriate.

                    context: {context},
                    question: {question}

                  """.replace("{chatbot_name}", chatbot_name),
    )

    llm = AzureChatOpenAI(
        openai_api_type="azure",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        temperature=0
    )

    # 4. Encapsulate the LLM and vectorstore in a RetrievalQA chain
    retrieval_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 60}),
        chain_type_kwargs={"prompt": prompt_template, "document_variable_name": "context"},
        return_source_documents=True
    )

    # 5. Define the query function
    result = retrieval_chain({"query": question})
    return {
        "answer": result["result"],
        "sources": [doc.metadata for doc in result["source_documents"]]
    }


# === Test the function ===
if __name__ == "__main__":
    res = query_with_langchain_rag("Which product has the lowest calories?", "assistant")
    print("Answer:", res["answer"])
    print("Sources:", res["sources"])
