from langchain.chains import LLMChain
from langchain.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from urllib.parse import quote_plus
import json
import re
from collections import defaultdict
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
    def __init__(self, chunks_json_path="rag/chunks.json", product_info_path="rag/brand_products.json"):
        self.chunks_json_path = chunks_json_path
        self.product_info_path = product_info_path
        self.product_links = {}
        self.brand_links = {}
        self.image_map = {}
        self._load_links()
        self._load_images()

    def _load_images(self):
        """
        More robust image loading with better error handling and normalization.
        """
        try:
            with open(self.product_info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"[DEBUG] Loading images from {self.product_info_path}")

            for brand_entry in data:
                brand_name = brand_entry.get("brand", "").strip()
                # print(f"[DEBUG] Processing brand: {brand_name}")

                for product in brand_entry.get("products", []):
                    name = product.get("name", "").strip()
                    img = product.get("image_url", "").strip()

                    if name and img:
                        # Store multiple variations of the product name
                        normalized_name = name.lower()
                        self.image_map[normalized_name] = img

                        # Also store with brand if available
                        if brand_name:
                            with_brand = f"{name} ({brand_name})".lower()
                            self.image_map[with_brand] = img

                            # Store brand + product format too
                            brand_product = f"{brand_name} {name}".lower()
                            self.image_map[brand_product] = img

                        # print(f"[DEBUG] Loaded image for: {name} -> {img}")

            print(f"[DEBUG] Total images loaded: {len(self.image_map)}")
            # print(f"[DEBUG] Image keys: {list(self.image_map.keys())}")

        except Exception as e:
            print(f"[ImageLoader] Failed to load: {e}")
            import traceback
            traceback.print_exc()

    def insert_product_images(self, answer_text):
        """
        Insert product images after Markdown links in the answer text.
        Fixed version that prevents duplicates and handles proper matching.
        """
        print(f"[DEBUG] Original answer_text length: {len(answer_text)}")
        # print(f"[DEBUG] Available images: {self.image_map.keys()}")

        # Track processed images to prevent duplicates
        processed_images = set()

        # Find all Markdown links first
        # Matching Markdown format: [**Product/Brand Name**](url)
        link_pattern_1 = re.compile(r'\[\*\*(.*?)\*\*\]\((.*?)\)', re.IGNORECASE)
        # Matching Markdown format: **[Product/Brand Name](url)**
        link_pattern_2 = re.compile(r'\*\*\[([^\]]+)\]\(([^)]+)\)\*\*', re.IGNORECASE)

        matches_1 = list(link_pattern_1.finditer(answer_text))
        matches_2 = list(link_pattern_2.finditer(answer_text))

        print(f"[DEBUG] Found format 1: {len(matches_1)} markdown links")
        print(f"[DEBUG] Found format 2: {len(matches_2)} markdown links")

        matches = matches_1 + matches_2

        # Process matches in reverse order to avoid position shifts
        for match in reversed(matches):
            link_text = match.group(1).strip()
            link_url = match.group(2).strip()
            full_match = match.group(0)

            print(f"[DEBUG] Processing link: '{link_text}' -> {link_url}")

            # Find matching image
            matched_image = None
            matched_key = None

            # Strategy 1: Exact match (case-insensitive)
            for img_key in self.image_map.keys():
                if link_text.lower() == img_key.lower():
                    matched_image = self.image_map[img_key]
                    matched_key = img_key
                    print(f"[DEBUG] Exact match found: {img_key}, URL: {matched_image}")
                    break

            # Strategy 2: Handle product names with brand info like "Product (Brand)"
            if not matched_image and '(' in link_text:
                product_part = link_text.split('(')[0].strip()
                for img_key in self.image_map.keys():
                    if product_part.lower() == img_key.lower():
                        matched_image = self.image_map[img_key]
                        matched_key = img_key
                        print(f"[DEBUG] Brand-aware exact match found: {img_key}")
                        break

            # Strategy 3: Partial match (be more selective)
            if not matched_image:
                for img_key in self.image_map.keys():
                    # Only match if the image key is a significant part of the link text
                    if (len(img_key) > 3 and img_key.lower() in link_text.lower() and
                            len(img_key) / len(link_text) > 0.5):
                        matched_image = self.image_map[img_key]
                        matched_key = img_key
                        print(f"[DEBUG] Selective partial match found: {img_key}")
                        break

            # Add image if found and not already processed
            if matched_image and matched_image not in processed_images:
                # Check if this exact image URL is already in the text
                if matched_image not in answer_text:
                    img_markdown = f"\n\n![{matched_key}]({matched_image})"
                    # Insert image right after the current link
                    insert_pos = match.end()

                    # Check if there's punctuation right after the matched link
                    if insert_pos < len(answer_text) and answer_text[insert_pos] in ",.;:!? ":
                        print(f"[DEBUG] Found punctuation after link: '{answer_text[insert_pos]}'")
                        insert_pos += 1  # move after punctuation

                    answer_text = (
                            answer_text[:insert_pos] +
                            img_markdown +
                            answer_text[insert_pos:]
                    )

                    processed_images.add(matched_image)
                    print(f"[DEBUG] Added image for: {link_text}")
                else:
                    print(f"[DEBUG] Image already in text, skipping: {matched_image}")
            elif matched_image:
                print(f"[DEBUG] Image already processed, skipping: {matched_image}")
            else:
                print(f"[DEBUG] No image found for: '{link_text}'")

        print("ANSWER TEXT AFTER IMAGE INSERTION:", answer_text)
        return answer_text

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

        except FileNotFoundError:
            print(f"Warning: {self.chunks_json_path} not found")
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {self.chunks_json_path}")

    def get_product_link(self, product_name, brand_name):
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
        return self.brand_links.get(brand_name.lower(), "")

    def extract_and_validate_links(self, response_text):
        # Extract the product name from the response and validate/replace the link
        # Matching Markdown format: [**Product/Brand Name**](url)
        link_pattern1 = r'\[\*\*(.*?)\*\*\]\((.*?)\)'

        # Matching Markdown format: **[Product/Brand Name](url)**
        link_pattern2 = r'\*\*\[([^\]]+)\]\(([^)]+)\)\*\*'

        def replace_link(match):
            display_text = match.group(1)
            current_url = match.group(2)

            # Try to extract product and brand from the display text
            # Format: "Product Name (Brand)" or "Product Name"
            if "(" in display_text and ")" in display_text:
                product_part = display_text.split("(")[0].strip()
                brand_part = display_text.split("(")[1].replace(")", "").strip()
            else:
                product_part = display_text.strip()
                brand_part = ""

            # Get the correct url
            product_info = self.get_product_link(product_part, brand_part)

            if product_info:
                correct_url = product_info["url"]
                correct_display = product_info["display_name"]
                return f"[**{correct_display}**]({correct_url})"
            else:
                # Fallback: if no link found, return the original match with warning
                print(f"WARNING: Could not find link for product: {display_text}")
                return match.group(0)

        # Substitute all links in the response text
        corrected_response = re.sub(link_pattern1, replace_link, response_text)
        corrected_response = re.sub(link_pattern2, replace_link, corrected_response)
        print(f"[DEBUG] Corrected response: {corrected_response, len(corrected_response)}")
        return corrected_response

def query_with_langchain_rag(question, chatbot_name, chat_history):
    # 0. Initialize the link manager if link validation is enabled
    link_manager = ProductLinkManager()

    # 1. Construct the embedding model
    embedding = AzureOpenAIEmbeddings(
        deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        openai_api_type="azure",
        chunk_size=16
    )

    # 2. Load the FAISS index
    vectorstore = FAISS.load_local("rag/faiss_index", embedding, allow_dangerous_deserialization=True)

    history_lines = []
    for msg in chat_history[-6:]:
        role = "User" if msg["sender"] == "user" else "Assistant"
        history_lines.append(f"{role}: {msg['text']}")

    history_str = "\\n".join(history_lines)

    # 3. Construct the LLM with enhanced prompt template
    prompt_template = PromptTemplate(
        input_variables=["context", "question", "history", "chatbot_name"],
        template="""
                    Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question no matter the question contains keywords such as "nestle".

                    Do not rely on your own knowledge or assumptions.
                    If the user asks for your name, respond with: "My name is {chatbot_name}, I'm your personal MadeWithNestle assistant."
                    Be concise, factual, and in English. **Do not say 'based on the context'**.
                    Only use content that is clearly relevant to the question.
                    Ignore irrelevant products or content even if they are nearby in the context.
                    
                    Generate a helpful, friendly and rich response for the user including:
                    - A well-written description of the product (tone: warm and informative)
                    - Mention 2-3 features
                    - A usage suggestion (e.g. when or who might enjoy this product)
                    - A follow-up question asking if the user would like to know more (e.g. nutrition details, nearby stores, similar products, etc.)
                    
                    Respond conversationally, like a real chat, you can also use emoji in the response BUT DO NOT USE EMOJI AS SINGLE BULLET LIST.

                    IMPORTANT: When providing product links, you MUST use the EXACT URL provided in the context for each product. Do not modify or generate URLs.

                    MUST FOLLOW THE INSTRUCTIONS BELOW:
                    1. Add "you can visit links:" before you provide the link.
                    2. If the answer contains product (brand) recommendations, show each product as a markdown hyperlink like [**Product (Brand) Name**](EXACT_URL_FROM_CONTEXT)
                    3. Use markdown formatting for links and bulleted lists where appropriate.
                    4. Ask for clarification if the question is ambiguous or too broad.
                    5. Do not hallucinate.
                    
                    Previous Conversation:
                    {history}

                    context: {context},
                    question: {question}

                  """.replace("{chatbot_name}", chatbot_name).replace("{history}", history_str)
    )

    llm = AzureChatOpenAI(
        openai_api_type="azure",
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        azure_deployment=AZURE_OPENAI_MODEL_DEPLOYMENT,
        temperature=0.5
    )

    # 4. Encapsulate the LLM and vectorstore in a RetrievalQA chain
    retrieval_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 10}),
        chain_type_kwargs={"prompt": prompt_template, "document_variable_name": "context"},
        return_source_documents=True
    )

    # 5. Define the query function
    res = retrieval_chain({"query": question})
    source_docs = res["source_documents"]

    product_map = defaultdict(lambda: {"url": None, "chunks": []})

    for doc in source_docs:
        pname = doc.metadata.get("product_name")
        purl = doc.metadata.get("product_url")
        if pname and purl:
            product_map[pname]["url"] = purl
            product_map[pname]["chunks"].append(doc.page_content)

    print("[DEBUG] Product Map:", product_map)

    multi_context = ""
    for pname, pdata in product_map.items():
        multi_context += f"=== {pname} ===\nURL: {pdata['url']}\n"
        multi_context += "\n".join(pdata["chunks"])
        multi_context += "\n\n"

    llm_chain = LLMChain(llm=llm, prompt=prompt_template)

    answer = llm_chain.run(
        context=multi_context,
        question=question,
        chatbot_name=chatbot_name,
        history=history_str
    )

    # 6. Verify and fix the url
    # answer = result["result"]
    # if validate_links and link_manager:
    answer = link_manager.extract_and_validate_links(answer)
    print("[DEBUG] Final answer after link validation:", answer)
    answer = link_manager.insert_product_images(answer)

    # 7. Prepare the references
    references = []
    seen_urls = set()
    for doc in source_docs:
        meta = doc.metadata
        if "product_name" in meta and "product_url" in meta:
            if meta["product_url"] not in seen_urls:
                references.append({
                    "title": f"{meta['product_name']} | Made with Nestlé Canada",
                    "url": meta["product_url"]
                })
                seen_urls.add(meta["product_url"])
        elif "brand" in meta and "brand_url" in meta:
            if meta["brand_url"] not in seen_urls:
                references.append({
                    "title": f"{meta['brand']} Brands' Products | Made With Nestlé Canada",
                    "url": meta["brand_url"]
                })
                seen_urls.add(meta["brand_url"])

    if references:
        references_md = "\n\n**Related Links**\n" + "\n".join(
            f"- [{ref['title']}]({ref['url']})" for ref in references
        )
        answer += references_md

    # 8. Format the sources
    return {
        "answer": answer,
        # "sources": references
    }

# === Test the function ===
if __name__ == "__main__":
    res = query_with_langchain_rag("can you introduce s'mores products", "assistant", [])
    print("Answer:", res["answer"])
    print("Sources:", res["Sources"])
