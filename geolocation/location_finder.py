from rest_framework.response import Response
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import math
import os
import json
from functools import lru_cache


# Mock data for stores and products
mock_stores = [
    {"name": "Walmart Toronto", "lat": 43.6532, "lon": -79.3832, "products": ["Kit Kat", "Coffee Crisp"]},
    {"name": "Shoppers Downtown", "lat": 43.6510, "lon": -79.3470, "products": ["Kit Kat", "Aero S'Mores Bars"]},
    {"name": "Loblaws", "lat": 43.6600, "lon": -79.4000, "products": ["Aero", "After Eight", "Kit Kat"]},
]

@lru_cache()
def load_brand_keywords():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, '../rag/brand_products.json')

    with open(json_path, 'r') as f:
        data = json.load(f)

    products_set = set()
    for brand in data:
        brand_name = brand.get('brand', '').strip().lower()
        if brand_name:
            products_set.add(brand_name)
            for products in brand.get('products', []):
                product_name = products.get('name', '').strip().lower()
                if product_name:
                    products_set.add(product_name)
    return list(products_set)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def stores_to_context(store_results, product):
    if not store_results:
        return f"No stores found nearby for {product}."
    return "\n".join([f"{s['name']} ({s['distance_km']} km away)" for s in store_results])

def location_query(question, lon, lat):
    product_keywords = load_brand_keywords()

    matched_product = next((kw for kw in product_keywords if kw in question), None)
    if not matched_product:
        return Response({"answer": "Sorry, I couldn't identify which product you're asking about."}, status=200)

    results = []
    for store in mock_stores:
        if any(matched_product in p.lower() for p in store["products"]):
            distance = haversine(lat, lon, store["lat"], store["lon"])
            # Not restrict to 10 km due to mock test purpose
            # if distance <= 10:
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
        temperature=0
    )

    prompt = [
        SystemMessage(
            content="Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question no matter the question contains keywords such as nestle."
                    "You need to mention all store info and distance away from the context."
                    "You need to be concise, factual, and in English. Do not say 'based on the context'."
                    "Use markdown formatting for links and bulleted lists where appropriate."),
        HumanMessage(content=f"The user asked: '{question}'\n\nAvailable stores:\n{store_info}")
    ]
    answer = llm(prompt).content

    return Response({"answer": answer}, status=200)
