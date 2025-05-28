import json
import re
from pathlib import Path

def ingredients_helper(text):
    # Preprocessing: Remove unwanted characters and patterns
    text = re.sub(r'\*.*?(?=\s|$)', '', text)  # Remove asterisk and its content
    text = re.sub(r'May contain:.*?(\.|$)', '', text, flags=re.IGNORECASE)  # Remove "May contain" and its content

    # Extract bracketed ingredients
    bracket_ingredients = re.findall(r'\((.*?)\)', text)

    # Split non-bracketed text by commas and periods
    non_bracket_text = re.sub(r'\(.*?\)', '', text)  # Remove bracketed text
    split_non_bracket = re.split(r'[,.]', non_bracket_text)

    # Merge bracketed and non-bracketed ingredients
    ingredients = []

    # Process bracketed ingredients
    for bracket in bracket_ingredients:
        ingredients.extend([i.strip() for i in re.split(r',\s*', bracket) if i.strip()])

    # Process non-bracketed ingredients
    for part in split_non_bracket:
        part = part.strip()
        if part and not part.startswith(('May contain', '*')):  # Ignore unwanted parts
            ingredients.append(part)

    # Remove duplicates while preserving order
    seen = set()
    return [x for x in ingredients if not (x.lower() in seen or seen.add(x.lower()))]


# === Split data into chunks ===
with open("rag/brand_products.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

chunks = []

for brand_block in raw_data:
    brand = brand_block.get("brand")
    category = brand_block.get("category")
    category_description = brand_block.get("category_description")
    products = brand_block.get("products", [])
    brand_url = brand_block.get("url", "")

    # --- Chunk 0: Brand metadata ---
    chunks.append({
            "metadata": {
                "brand": brand,
                "brand_url": brand_url,
                "category": category,
                "chunk_type": "Brand metadata",
            },
            "content": f"\"{brand}\" is a brand from Nestle company, it belongs to \"{category}\" category. The URL (link) of this brand is: {brand_url}",
        })

    for product in products:
        name = product.get("name")
        specification = product.get("specification")
        status = product.get("status", "Regular")
        product_url = product.get("product_url", "")

        # --- Chunk 1: product_metadata ---
        meta_content = f"\"{name}\" is a product belongs to \"{brand}\" brand. The url (link) of this product is: {product_url}."
        if status:
            meta_content += f" It is the {status} product."

        chunks.append({
            "metadata": {
                "brand": brand,
                "product_name": name,
                "brand_url": brand_url,
                "product_url": product_url,
                "category": category,
                "chunk_type": "product_metadata",
                **({"status": status} if status else {})
            },
            "content": meta_content
        })

        # --- Chunk 2: core_desc ---
        description = product.get("description", "")
        if description:
            desc_short = description.split(".")[0].strip()  # First sentence
            chunks.append({
                "metadata": {
                    "brand": brand,
                    "brand_url": brand_url,
                    "product_url": product_url,
                    "product_name": name,
                    "chunk_type": "core_desc",
                    "specification": specification
                },
                "content": f"{name} ({specification}): {desc_short}."
            })

        # --- Chunk 3: nutrition (one per nutrient) ---
        nutrition_list = product.get("nutrition", [])
        for item in nutrition_list:
            field = item.get("type", "").strip().lower()
            amount = item.get("amount", "").strip()
            dv = item.get("dv", "").strip()

            nu_content = f"{name} from {brand} has {amount} {field} and dv is {dv}."
            if not dv:
                nu_content = f"{name} from {brand} has {amount} {field} and dv is not provided."

            if field and amount:
                chunks.append({
                    "metadata": {
                        "brand": brand,
                        "product_name": name,
                        "brand_url": brand_url,
                        "product_url": product_url,
                        "chunk_type": "nutrition",
                        "field": field,
                        "amount": amount,
                        "dv": dv
                    },
                    "content": nu_content
                })

        # --- Chunk 4: features ---
        features = product.get("features", "")
        feature_lines = features.strip().split("\n")
        for line in feature_lines:
            if line.strip():
                field = line.split(":")[0].strip() if ":" in line else line.strip()
                chunks.append({
                    "metadata": {
                        "brand": brand,
                        "product_name": name,
                        "brand_url": brand_url,
                        "product_url": product_url,
                        "chunk_type": "features",
                        "field": field
                    },
                    "content": f"{name} has the feature: {field}"
                })

        # --- Chunk 5: ingredients ---
        ingredients = product.get("ingredient", "")
        if ingredients:
            ingredient_lines = ingredients_helper(ingredients)
            for line in ingredient_lines:
                if line.strip():
                    field = line.strip()
                    chunks.append({
                        "metadata": {
                            "brand": brand,
                            "product_name": name,
                            "brand_url": brand_url,
                            "product_url": product_url,
                            "chunk_type": "ingredients",
                            "field": field
                        },
                        "content": f"{name} has the ingredients: {field}"
                    })
        else:
            chunks.append({
                "metadata": {
                    "brand": brand,
                    "product_name": name,
                    "brand_url": brand_url,
                    "product_url": product_url,
                    "chunk_type": "ingredients",
                    "field": "Not provided"
                },
                "content": f"The ingredients of {name} are not provided."
            })

        # --- Chunk 6: category ---
        chunks.append({
            "metadata": {
                "brand": brand,
                "product_name": name,
                "brand_url": brand_url,
                "product_url": product_url,
                "chunk_type": "category",
                "field": category
            },
            "content": f"{name} belongs to the {category} category."
        })



# === Save as chunks.json ===
output_path = Path("rag/chunks.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"Finished: {len(chunks)} chunks saved to rag/chunks.json")
