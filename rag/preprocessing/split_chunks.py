import json
from pathlib import Path

with open("rag/data.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

chunks = []

# === Split data into chunks ===
for brand_block in raw_data:
    brand = brand_block.get("brand")
    category = brand_block.get("category")
    products = brand_block.get("products", [])
    brand_url = brand_block.get("url", "")

    # --- Chunk 0: brand_metadata ---
    for product in products:
        name = product.get("name")
        specification = product.get("specification")
        status = product.get("status", None)
        product_url = product.get("product_url", "")

        # --- Chunk 1: product_metadata ---
        meta_content = f"Brand: {brand} | Category: {category} | Product: {name}"
        if status:
            meta_content += f" | Status: {status}"

        chunks.append({
            "metadata": {
                "brand": brand,
                "product_name": name,
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
                "content": f"{name} ({specification}): {desc_short}"
            })

        # --- Chunk 3: nutrition ---
        nutrition = product.get("nutrition", {})
        if nutrition:
            nutri_fields = list(nutrition.items())
            nutri_content = " | ".join([f"{k}: {v}" for k, v in nutri_fields])
            chunks.append({
                "metadata": {
                    "brand": brand,
                    "product_name": name,
                    "chunk_type": "nutrition",
                    "field": ", ".join([k for k, _ in nutri_fields])
                },
                "content": nutri_content
            })

        # --- Chunk 4: features ---
        features = product.get("features", "")
        feature_lines = features.strip().split("\n")
        for line in feature_lines:
            if line.strip():
                field = line.split(":")[0].strip() if ":" in line else "feature"
                chunks.append({
                    "metadata": {
                        "brand": brand,
                        "product_name": name,
                        "chunk_type": "features",
                        "field": field
                    },
                    "content": line.strip()
                })

# === Save as chunks.json ===
output_path = Path("rag/chunks.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"Finished: {len(chunks)} chunks saved to metadata.json")
