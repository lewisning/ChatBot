from langchain.chains.llm import LLMChain
from langchain.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from urllib.parse import quote_plus
import json
import re
from typing import Dict, List, Tuple

# === Azure OpenAI Configure ===
from dotenv import load_dotenv
import os

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
AZURE_OPENAI_MODEL_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")


class ProductLinkManager:
    def __init__(self, chunks_json_path="rag/chunks.json"):
        self.chunks_json_path = chunks_json_path
        self.product_links = {}
        self.brand_links = {}
        self._load_links()

    def _load_links(self):
        # Load all product and brand links from the chunks.json file
        try:
            with open(self.chunks_json_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)

            for chunk in chunks:
                metadata = chunk.get("metadata", {})

                # Store brand links
                if "brand" in metadata and "brand_url" in metadata:
                    brand = metadata["brand"]
                    brand_url = metadata["brand_url"]
                    self.brand_links[brand.lower()] = brand_url

                # Store product links
                if "product_name" in metadata and "product_url" in metadata:
                    product = metadata["product_name"]
                    product_url = metadata["product_url"]
                    brand = metadata.get("brand", "")

                    # Use both product and brand to create a unique key
                    key = f"{product.lower()}_{brand.lower()}".strip("_")
                    self.product_links[key] = {
                        "url": product_url,
                        "display_name": f"{product} ({brand})" if brand else product,
                        "brand": brand
                    }

                    # Store the product name alone for cases where brand is not provided as well
                    self.product_links[product.lower()] = {
                        "url": product_url,
                        "display_name": f"{product} ({brand})" if brand else product,
                        "brand": brand
                    }
            print(self.product_links)

        except FileNotFoundError:
            print(f"Warning: {self.chunks_json_path} not found")
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {self.chunks_json_path}")

    def get_product_link(self, product_name, brand_name):
        """获取产品链接信息"""
        # 尝试不同的键组合
        keys_to_try = [
            f"{product_name.lower()}_{brand_name.lower()}".strip("_"),
            product_name.lower(),
            f"{brand_name.lower()}_{product_name.lower()}".strip("_")
        ]

        for key in keys_to_try:
            if key in self.product_links:
                return self.product_links[key]

        return None

    def get_brand_link(self, brand_name):
        """获取品牌链接"""
        return self.brand_links.get(brand_name.lower(), "")

    def extract_and_validate_links(self, response_text):
        """从响应中提取产品名称并验证/替换链接"""
        # 匹配markdown链接格式 [**Product (Brand) Name**](url)
        link_pattern = r'\[\*\*(.*?)\*\*\]\((.*?)\)'

        def replace_link(match):
            display_text = match.group(1)
            current_url = match.group(2)

            # 尝试从显示文本中提取产品名和品牌名
            # 假设格式是 "Product Name (Brand)" 或 "Product Name"
            if "(" in display_text and ")" in display_text:
                product_part = display_text.split("(")[0].strip()
                brand_part = display_text.split("(")[1].replace(")", "").strip()
            else:
                product_part = display_text.strip()
                brand_part = ""

            # 获取正确的链接
            product_info = self.get_product_link(product_part, brand_part)

            if product_info:
                correct_url = product_info["url"]
                correct_display = product_info["display_name"]
                return f"[**{correct_display}**]({correct_url})"
            else:
                # 如果找不到匹配的产品，保持原样但记录警告
                print(f"Warning: Could not find link for product: {display_text}")
                return match.group(0)

        # 替换所有链接
        corrected_response = re.sub(link_pattern, replace_link, response_text)
        return corrected_response

def query_with_langchain_rag(question, chatbot_name, validate_links=True):
    # 初始化链接管理器
    link_manager = ProductLinkManager() if validate_links else None

    # 1. Construct the embedding model
    embedding = AzureOpenAIEmbeddings(
        deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        openai_api_type="azure",
        chunk_size=16
    )

    # 2. Load the FAISS index
    vectorstore = FAISS.load_local("rag/faiss_index", embedding, allow_dangerous_deserialization=True)

    # 3. Construct the LLM
    # 修改prompt模板，强调使用准确的URL
    prompt_template = PromptTemplate(
        input_variables=["context", "question", "chatbot_name"],
        template="""
                    Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question no matter the question contains keywords such as "nestle".

                    Do not rely on your own knowledge or assumptions.
                    If the user asks for your name, respond with: "My name is {chatbot_name}, I'm your personal MadeWithNestle assistant."
                    Be concise, factual, and in English. **Do not say 'based on the context'**.
                    Only use content that is clearly relevant to the question.
                    Ignore irrelevant products or content even if they are nearby in the context.

                    IMPORTANT: When providing product links, you MUST use the EXACT URL provided in the context for each product. Do not modify or generate URLs.

                    Please format your answer based on the type:
                    1. If the answer contains **product (brand) recommendations**, show each product as a markdown hyperlink like [**Product (Brand) Name**](EXACT_URL_FROM_CONTEXT) and add "you can visit following links:" before you provide the link.
                    2. If the answer contains **factual or informational content**, insert markdown hyperlinks directly inside the text, and add a citation number in format of [1], [2] ... etc. after each link **inside the text**.
                    Do not include a "References" section at the end of the message.
                    Use markdown formatting for links and bulleted lists where appropriate.

                    context: {context},
                    question: {question}

                  """.replace("{chatbot_name}", chatbot_name),
    )

    llm = AzureChatOpenAI(
        openai_api_type="azure",
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        azure_deployment=AZURE_OPENAI_MODEL_DEPLOYMENT,
        temperature=0.2,
        max_tokens=1000
    )

    # 4. Encapsulate the LLM and vectorstore in a RetrievalQA chain
    retrieval_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 10}),
        chain_type_kwargs={"prompt": prompt_template, "document_variable_name": "context"},
        return_source_documents=True
    )

    # 5. Define the query function
    result = retrieval_chain({"query": question})

    # 6. 验证和修正链接（如果启用）
    answer = result["result"]
    if validate_links and link_manager:
        answer = link_manager.extract_and_validate_links(answer)

    return {
        "answer": answer,
        "sources": [doc.metadata for doc in result["source_documents"]]
    }

# === Test the function ===
if __name__ == "__main__":
    res = query_with_langchain_rag("can you introduce s'mores products", "assistant")
    print("Answer:", res["answer"])
    # print("Sources:", res["sources"])
