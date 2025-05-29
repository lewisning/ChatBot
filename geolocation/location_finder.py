from rest_framework.response import Response
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import math
import os
from urllib.parse import quote_plus
import json
from functools import lru_cache
from rag.langchain.name_match import product_match

# Mock data for stores and products
with open("./rag/mock_stores.json", 'r') as f:
    mock_stores = json.load(f)

# @lru_cache()
# def load_brand_keywords():
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     json_path = os.path.join(base_dir, '../rag/brand_products.json')
#
#     with open(json_path, 'r') as f:
#         data = json.load(f)
#
#     products_set = set()
#     for brand in data:
#         brand_name = brand.get('brand', '').strip().lower()
#         if brand_name:
#             products_set.add(brand_name)
#             for products in brand.get('products', []):
#                 product_name = products.get('name', '').strip().lower()
#                 if product_name:
#                     products_set.add(product_name)
#     return list(products_set)

@lru_cache()
def load_brand_keywords():
    with open("./rag/brand_products.json", 'r') as f:
        data = json.load(f)

    products_set = set()
    product_to_brand = {}

    for brand in data:
        brand_name = brand.get('brand', '').strip().lower()
        if brand_name:
            products_set.add(brand_name)
            for products in brand.get('products', []):
                product_name = products.get('name', '').strip().lower()
                if product_name:
                    products_set.add(product_name)
                    product_to_brand[product_name] = brand_name

    return list(products_set), product_to_brand


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def get_amazon_link(product, brand):
    # This function should return the Amazon link for the product
    # Due to don't have Amazon Product Advertising API access, I hard code the link format
    return f"https://www.amazon.ca/s?k={quote_plus(product)}+{quote_plus(brand)}"

def stores_to_context(store_results, product):
    if not store_results:
        return f"No stores found nearby for {product}."
    return "\n".join([f"{s['name']} ({s['distance_km']} km away)" for s in store_results])

def location_query(question, lon, lat):
    product_keywords, product_to_brand = load_brand_keywords()
    # print("\n\n\n",product_keywords,"\n\n\n")
    # print("\n\n\n", product_to_brand, "\n\n\n")

    matched_product = product_match(question, product_keywords)
    if not matched_product:
        return Response({"answer": "Sorry, I couldn't identify which product you're asking about.\n\nYou can find more information on [madewithnestle](https://www.madewithnestle.ca/)."}, status=200)

    brand = product_to_brand.get(matched_product, matched_product)

    amazon_link = get_amazon_link(matched_product, brand)

    results = []
    for store in mock_stores:
        if any(matched_product in p.lower() for p in store["products"]):
            distance = haversine(lat, lon, store["lat"], store["lon"])
            # For testing use, we assume a maximum distance of 90 km, normally will be 10 km
            if distance > 90:
                continue
            results.append({
                "name": store["name"],
                "distance_km": round(distance, 2)
            })

    store_info = stores_to_context(results, matched_product)

    llm = AzureChatOpenAI(
        openai_api_type="azure",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        temperature=0.2
    )

    prompt = [
        SystemMessage(
            content=f"""Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question no matter the question contains keywords such as nestle.
                    You need to mention all store info and distance away from the context.
                    
                    FOLLOW EXACTLY THE INSTRUCTIONS BELOW:
                    
                    context:
                    Available stores:\n{store_info}
                    Amazon link: {amazon_link}
                    
                    YOUR RESPONSE FORMAT:
                    - If the answer contains **store locator**, provide a concise list of stores with their distances.
                    - You need to be concise, factual, and in English. Do not say 'based on the context'.
                    - Use markdown formatting for links and bulleted lists where appropriate and each item in the list is a new line, not the new paragraph.
                    - DO NOT START WITH THE MARKDOWN LIST, START WITH A SENTENCE TO INTRODUCE THE LIST.
                    - Add Amazon link for the product after all listed stores. The format is: You can also [purchase on Amazon]({amazon_link})."""),
        HumanMessage(
            content=f"The user asked: '{question}'")
    ]

    answer = llm(prompt).content

    return Response({"answer": answer}, status=200)
