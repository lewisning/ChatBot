from rest_framework.response import Response
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import math
import os
import re
from urllib.parse import quote_plus
import json
from functools import lru_cache

from rag.langchain.name_match import product_match

# Mock data for stores and products
with open("./rag/mock_stores.json", 'r') as f:
    mock_stores = json.load(f)

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

def extract_latest_product_from_history(chat_history):
    products = set()
    for msg in reversed(chat_history):
        if msg.get("sender") == "bot":
            text = msg.get("text", "")
            matches = re.findall(r"\[\*\*(.*?)\*\*\]\(.*?\)", text)
            if matches:
                for name in matches:
                    product = name.split("(")[0].strip()
                    products.add(product.lower())
            matches_bold = re.findall(r"\*\*(.*?)\*\*", text)
            if matches_bold:
                for name in matches_bold:
                    product = name.split("(")[0].strip()
                    products.add(product.lower())
    return list(products) if products else None


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

def location_query(question, lon, lat, chat_history):
    product_keywords, product_to_brand = load_brand_keywords()

    matched_product = product_match(question, product_keywords, chat_history)
    print("MATCHED PRODUCT:", matched_product)
    if not matched_product:
        matched_product = extract_latest_product_from_history(chat_history)

    print("HISTORY:", chat_history[-1] if chat_history else "No history")
    print("MATCHED:", matched_product)

    if not matched_product:
        return Response({"answer": "Sorry, I couldn't identify which product you're asking about.\n\nYou can find more information on [madewithnestle](https://www.madewithnestle.ca/)."}, status=200)

    productlink_dict = {}
    for product in matched_product:
        brand = product_to_brand.get(product, product)
        amazon_link = get_amazon_link(product, brand)
        productlink_dict[product] = amazon_link

    results = []
    for product in matched_product:
        print("\n\nPROCESSING PRODUCTS:", product)
        if '[' in product or ']' in product:
            product = product.replace('[', '').replace(']', '').strip()

        brand = product_to_brand.get(product.lower(), product)
        amazon_link = get_amazon_link(product, brand)

        store_results = []
        for store in mock_stores:
            if any(product.lower() in p.lower() for p in store["products"]):
                print(f"Checking store: {store['name']} for product: {product}")
                distance = haversine(lat, lon, store["lat"], store["lon"])
                # if distance <= 90:
                store_results.append({
                    "name": store["name"],
                    "distance_km": round(distance, 2)
                })
        results.append({
            "product": product,
            "brand": brand,
            "amazon_link": amazon_link,
            "stores": store_results
        })

    print("RESULTS:", results)

    store_info = ""
    for res in results:
        store_list = "\n".join([f"- {s['name']} ({s['distance_km']} km away)" for s in res['stores']])
        store_info += f"\n### {res['product']}\n{store_list}\nAmazon link: {res['amazon_link']}\n"

    llm = AzureChatOpenAI(
        openai_api_type="azure",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        temperature=0.3
    )

    prompt = [
        SystemMessage(
            content=f"""Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question no matter the question contains keywords such as nestle.
                    You need to mention all store info and distance away from the context.
                    
                    FOLLOW EXACTLY THE INSTRUCTIONS BELOW:
                    Generate a helpful, friendly and rich response for the user including:
                    - A well-written description of the product (tone: warm and informative)
                    - Mention 2-3 features
                    - A usage suggestion (e.g. when or who might enjoy this product)
                    - A follow-up question asking if the user would like to know more (e.g. nutrition details, nearby stores, similar products, etc.)
                    
                    Respond conversationally, like a real chat, you can also use appropriate emoji in the response.
                    
                    context:
                    Available stores:\n{store_info}
                    
                    YOUR RESPONSE FORMAT:
                    - If the answer contains **store locator**, provide a concise list of stores with their distances.
                    - You need to be concise, factual, and in English. Do not say 'based on the context'.
                    - Use markdown formatting for links and bulleted lists where appropriate and each item in the list is a new line, not the new paragraph.
                    - Respond conversationally, using markdown formatting.
                    - Add Amazon link for the product after all listed stores. The format is: You can also [purchase on Amazon]({amazon_link})."""),
        HumanMessage(
            content=f"The user asked: '{question}', the previous conversation history is: {chat_history}.")
    ]

    answer = llm(prompt).content

    return Response({"answer": answer}, status=200)

if __name__ == "__main__":
    # data = [{'sender': 'user', 'text': 'any recommendation?', 'time': '14:38'}, {'sender': 'bot',
    #                                                                       'text': "Hello! If you're looking for a delightful treat, I have a couple of recommendations that might just hit the spot:\n\n- [**KitKat MEGA (Kit Kat)**](https://www.madewithnestle.ca/kit-kat/kitkat-mega): This is the perfect treat for sharing with friends or family. It's Rainforest Alliance Certified, ensuring that you're enjoying a product made with sustainable practices. Loved worldwide, this KitKat is sure to bring a smile to anyone's face. It's great for gatherings or just a cozy night in with loved ones.\n\n- [**KITKAT Classic Tablet (Kit Kat)**](https://www.madewithnestle.ca/kit-kat/kitkat-classic-tablet): Experience a multisensory snacking delight with this classic treat. Made with quality ingredients and also Rainforest Alliance Certified, it's a snack you can feel good about enjoying. Perfect for a quick break during a busy day or as a sweet treat after dinner.\n\nWould you like to know more about these products, such as nutrition details or where you can find them nearby?",
    #                                                                       'time': '14:38', 'refs': []}]
    # extract = extract_latest_product_from_history(data)
    #
    # print("Extracted Product:", extract)
    question = "Where can I find KitKat MEGA?"
    lon, lat = -79.3832, 43.6532  # Example coordinates for Toronto
    chat_history = [{'sender': 'user', 'text': 'Where can I find KitKat MEGA?', 'time': '14:38'}]
    response = location_query(question, lon, lat, chat_history)
    print("Response:", response.data.get("answer"))
