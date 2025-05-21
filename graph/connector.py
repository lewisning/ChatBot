import json
import re
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
graph_username = os.getenv("NEO4J_USERNAME")
graph_password = os.getenv("NEO4J_PASSWORD")
graph_uri = os.getenv("NEO4J_URI")

class GraphConnector:
    def __init__(self, uri=graph_uri, user=graph_username, password=graph_password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_brand_product_graph(self, chunk):
        with self.driver.session() as session:
            meta = chunk["metadata"]
            chunk_type = meta.get("chunk_type", "")
            brand = meta.get("brand")
            product = meta.get("product_name", "")
            brand_url = meta.get("brand_url", "")
            product_url = meta.get("product_url", "")

            # === Node 1: Brand ===
            if chunk_type == "Brand metadata":
                session.run(
                    """
                    MERGE (b:Brand {name: $brand})
                    SET b.url = $brand_url,
                        b.category = $category
                    """,
                    brand=brand,
                    brand_url=brand_url,
                    category=meta.get("category", "")
                )

            # === Node 2: Product Introduction ===
            elif chunk_type == "product_metadata":
                session.run(
                    """
                    MATCH (b:Brand {name: $brand})
                    MERGE (p:Product {name: $product})
                    SET p.category = $category,
                        p.status = $status
                    MERGE (b)-[:OWNS]->(p)
                    """,
                    brand=brand,
                    product=product,
                    category=meta.get("category", ""),
                    status=meta.get("status", "")
                )

            # === Node 3: Product Description ===
            elif chunk_type == "core_desc":
                session.run(
                    """
                    MATCH (p:Product {name: $product})
                    SET p.specification = $specification,
                        p.url = $product_url
                    """,
                    product=product,
                    specification=meta.get("specification", ""),
                    product_url=product_url
                )

            # === Node 4: Nutrition ===
            elif chunk_type == "nutrition":
                nutrition_name = meta.get("field")
                value = meta.get("amount", "").strip()
                dv = meta.get("dv", "").strip()

                # Split the value into numeric and unit parts
                match = re.match(r"([\d.]+)\s*([a-zA-Z]*)", value)
                numeric_value = match.group(1) if match else value
                unit = match.group(2) if match else ""

                session.run(
                    """
                    MATCH (p:Product {name: $product})
                    MERGE (n:Nutrition {name: $nutrition_name, value: $value, unit: $unit, daily_percent: $dv})
                    MERGE (p)-[:HAS_NUTRITION]->(n)
                    """,
                    product=product,
                    nutrition_name=nutrition_name,
                    value=numeric_value,
                    unit=unit,
                    dv=dv
                )

            # === Node 5: Product Features ===
            elif chunk_type == "features":
                feature = meta.get("field", "")
                if feature:
                    session.run(
                        """
                        MATCH (p:Product {name: $product})
                        MERGE (f:Feature {name: $feature})
                        MERGE (p)-[:HAS_FEATURE]->(f)
                        """,
                        product=product,
                        feature=feature
                    )

            # === Node 6: Product Ingredients ===
            elif chunk_type == "ingredients":
                ingredient = meta.get("field", "")
                if ingredient:
                    session.run(
                        """
                        MATCH (p:Product {name: $product})
                        MERGE (i:Ingredient {name: $ingredient})
                        MERGE (p)-[:HAS_INGREDIENT]->(i)
                        """,
                        product=product,
                        ingredient=ingredient
                    )

def load_and_ingest_optimized(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    brands_data = [raw_data] if isinstance(raw_data, dict) else raw_data

    connector = GraphConnector()
    for brand in brands_data:
        try:
            connector.create_brand_product_graph(brand)
        except Exception as e:
            print(f"FAILED to import: {e}")
    connector.close()
    print(f"SUCCESS: {len(brands_data)} records imported.")

if __name__ == "__main__":
    load_and_ingest_optimized("rag/chunks.json")
