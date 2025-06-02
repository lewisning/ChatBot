from rest_framework.response import Response
from langchain.chat_models import AzureChatOpenAI
from langchain.graphs import Neo4jGraph
from langchain.schema import SystemMessage, HumanMessage
from langchain.chains import GraphCypherQAChain
import os
import re
import json
from dotenv import load_dotenv
from typing import List, Dict, Optional, Tuple
from neo4j import GraphDatabase

# Initialize Azure OpenAI
load_dotenv()


class EnhancedGraphRAG:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            openai_api_type="azure",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            temperature=0,
            n=1
        )

        self.graph = Neo4jGraph(
            url=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD")
        )

        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )

        # Construct the dynamic schema and query examples
        self.schema_info = self._build_dynamic_schema()
        self.query_examples = self._load_query_examples()

    def _build_dynamic_schema(self):
        """Dynamically construct the schema from Neo4j"""
        try:
            with self.driver.session() as session:
                # GET node labels and properties
                node_query = """
                CALL db.labels() YIELD label
                CALL {
                    WITH label
                    CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN keys(n) as props', {}) YIELD value
                    RETURN label, value.props as properties
                }
                RETURN label, properties
                """

                # GET relationship types
                rel_query = """
                CALL db.relationshipTypes() YIELD relationshipType
                RETURN relationshipType
                """

                try:
                    nodes = session.run(node_query).data()
                except:
                    # Use default schema if APOC dynamic query fails
                    nodes = [
                        {"label": "Brand", "properties": ["name", "category", "url"]},
                        {"label": "Product", "properties": ["name", "specification", "category", "url", "status"]},
                        {"label": "Nutrition", "properties": ["unit", "name", "daily_percent", "value"]},
                        {"label": "Feature", "properties": ["name"]},
                        {"label": "Ingredient", "properties": ["name"]},
                        {"label": "Category", "properties": ["name"]}
                    ]

                relationships = session.run(rel_query).data()

                return {
                    "nodes": nodes,
                    "relationships": [r["relationshipType"] for r in relationships]
                }
        except Exception as e:
            print(f"[WARNING] Schema discovery failed: {e}")
            # Return a default schema if discovery fails
            return {
                "nodes": [
                    {"label": "Brand", "properties": ["name", "category", "url"]},
                    {"label": "Product", "properties": ["name", "specification", "category", "url", "status"]},
                    {"label": "Nutrition", "properties": ["unit", "name", "daily_percent", "value"]},
                    {"label": "Feature", "properties": ["name"]},
                    {"label": "Ingredient", "properties": ["name"]},
                    {"label": "Category", "properties": ["name"]}
                ],
                "relationships": ["OWNS", "HAS_NUTRITION", "HAS_FEATURE", "HAS_INGREDIENT", "BELONGS_TO"]
            }

    def _load_query_examples(self):
        """Load predefined query examples"""
        return [
            {
                "question": "show me products with high protein",
                "cypher": "MATCH (p:Product)-[:HAS_NUTRITION]->(n:Nutrition) WHERE toLower(n.name) = 'protein' AND toFloat(n.value) > 10 RETURN p.name, p.url, n.value ORDER BY toFloat(n.value) DESC",
                "intent": "nutrition_filter"
            },
            {
                "question": "what products does nestle own",
                "cypher": "MATCH (b:Brand)-[:OWNS]->(p:Product) WHERE toLower(b.name) CONTAINS 'nestle' RETURN p.name, p.url, p.category",
                "intent": "brand_products"
            },
            {
                "question": "find products with low calories",
                "cypher": "MATCH (p:Product)-[:HAS_NUTRITION]->(n:Nutrition) WHERE toLower(n.name) = 'calories' AND toFloat(n.value) < 100 RETURN p.name, p.url, n.value ORDER BY toFloat(n.value) ASC",
                "intent": "nutrition_filter"
            },
            {
                "question": "show me dairy products",
                "cypher": "MATCH (p:Product) WHERE toLower(p.category) CONTAINS 'dairy' OR toLower(p.name) CONTAINS 'milk' RETURN p.name, p.url, p.category",
                "intent": "category_search"
            },
            {
                "question": "products with vitamin c",
                "cypher": "MATCH (p:Product)-[:HAS_NUTRITION]->(n:Nutrition) WHERE toLower(n.name) CONTAINS 'vitamin c' RETURN p.name, p.url, n.value",
                "intent": "nutrition_search"
            }
        ]

    def _classify_query_intent(self, question):
        """Simple intent classification based on keywords"""
        question_lower = question.lower()

        if any(word in question_lower for word in
               ['protein', 'calories', 'fat', 'sodium', 'sugar', 'vitamin', 'nutrition']):
            return "nutrition_query"
        elif any(word in question_lower for word in ['brand', 'nestle', 'owns', 'company']):
            return "brand_query"
        elif any(word in question_lower for word in ['category', 'type', 'dairy', 'snack', 'beverage']):
            return "category_query"
        elif any(word in question_lower for word in ['ingredient', 'contains', 'made with']):
            return "ingredient_query"
        else:
            return "general_query"

    def _extract_entities(self, question):
        """Extract entities from the question using simple keyword matching"""
        entities = {
            "nutrition_names": [],
            "product_names": [],
            "brand_names": [],
            "numbers": []
        }

        # Nutrition keywords
        nutrition_keywords = ['protein', 'calories', 'fat', 'saturated fat', 'trans fat', 'sodium', 'cholesterol', 'sodium', 'carbohydrate', 'sugar', 'vitamin', 'dietary fiber', 'iron', 'potassium', 'calcium']
        for keyword in nutrition_keywords:
            if keyword in question.lower():
                entities["nutrition_names"].append(keyword)

        # Brand keywords
        brand_keywords = ['nestle', 'nestlé', 'aero', 'coffee crisp', 'after eight', 'big turk', 'kit kat',]
        for keyword in brand_keywords:
            if keyword in question.lower():
                entities["brand_names"].append(keyword)

        # Extract product names
        numbers = re.findall(r'\d+', question)
        entities["numbers"] = [int(n) for n in numbers]

        return entities

    def _validate_cypher_syntax(self, cypher):
        """Validate Cypher syntax and check for dangerous operations"""
        try:
            # Basic validation
            if not cypher.strip():
                return False, "Empty query"

            # Check for dangerous operations
            dangerous_keywords = ['CREATE', 'DELETE', 'MERGE', 'SET', 'REMOVE', 'DROP']
            for keyword in dangerous_keywords:
                if keyword.upper() in cypher.upper():
                    return False, f"Dangerous operation detected: {keyword}"

            # Try to explain the query to check syntax
            with self.driver.session() as session:
                explain_query = f"EXPLAIN {cypher}"
                session.run(explain_query)
                return True, "Valid"

        except Exception as e:
            return False, str(e)

    def _test_cypher_execution(self, cypher):
        """Test Cypher execution"""
        try:
            with self.driver.session() as session:
                # Add LIMIT to avoid long-running queries
                test_cypher = cypher
                if "LIMIT" not in cypher.upper():
                    test_cypher += " LIMIT 5"

                result = session.run(test_cypher)
                data = result.data()
                return True, data
        except Exception as e:
            return False, str(e)

    def _build_enhanced_prompt(self, question, entities, intent):
        """Construct an enhanced prompt for Cypher generation"""

        # GET relevant examples based on intent
        relevant_examples = [ex for ex in self.query_examples if ex["intent"] in [intent, "general_query"]][:3]

        examples_text = "\n".join([
            f"Question: {ex['question']}\nCypher: {ex['cypher']}\n"
            for ex in relevant_examples
        ])

        schema_text = f"""
        Nodes: {[f"{node['label']}: {node['properties']}" for node in self.schema_info['nodes']]}
        Relationships: {self.schema_info['relationships']}
        """

        return f"""
                You are a Cypher expert. Generate ONLY READ-ONLY Cypher queries for Neo4j.
        
                CRITICAL RULES:
                1. ALL property values in the database are in LOWERCASE
                2. Always use toLower() when comparing strings
                3. Use toFloat() when comparing numbers
                4. Only use MATCH, WHERE, RETURN, ORDER BY, LIMIT
                5. NO CREATE, DELETE, MERGE, SET operations
        
                Database Schema:
                {schema_text}
        
                Query Examples:
                {examples_text}
        
                Detected Intent: {intent}
                Extracted Entities: {entities}
        
                Question: {question}
        
                Generate a single, optimized Cypher query that directly answers the question.
                Focus on accuracy and performance.
        
                Cypher:
                """

    def _generate_multiple_candidates(self, question):
        """Generate multiple Cypher query candidates"""
        entities = self._extract_entities(question)
        intent = self._classify_query_intent(question)

        candidates = []

        # Method 1: Enhanced prompt with LLM
        enhanced_prompt = self._build_enhanced_prompt(question, entities, intent)
        messages = [HumanMessage(content=enhanced_prompt)]
        response1 = self.llm.invoke(messages)
        candidates.append(response1.content.strip())

        # Method 2: Template-based generation
        template_cypher = self._template_based_generation(question, entities, intent)
        if template_cypher:
            candidates.append(template_cypher)

        # Method 3: Simple prompt for fallback (Backup)
        simple_prompt = f"""
                        Generate a Neo4j Cypher query for: {question}
                
                        Schema: Brand-[:OWNS]->Product-[:HAS_NUTRITION]->Nutrition
                
                        Rules:
                        - Use toLower() for string comparisons
                        - All values are lowercase in database
                        - Only READ operations
                
                        Cypher:
                        """
        messages = [HumanMessage(content=simple_prompt)]
        response2 = self.llm.invoke(messages)
        candidates.append(response2.content.strip())

        return candidates

    def _template_based_generation(self, question, entities, intent):
        """Generate Cypher using predefined templates based on intent and entities"""
        templates = {
            "nutrition_query": "MATCH (p:Product)-[:HAS_NUTRITION]->(n:Nutrition) WHERE toLower(n.name) = '{nutrition}' RETURN p.name, p.url, n.value",
            "brand_query": "MATCH (b:Brand)-[:OWNS]->(p:Product) WHERE toLower(b.name) CONTAINS '{brand}' RETURN p.name, p.url",
            "category_query": "MATCH (p:Product) WHERE toLower(p.category) CONTAINS '{category}' RETURN p.name, p.url"
        }

        if intent == "nutrition_query" and entities.get("nutrition_names"):
            return templates["nutrition_query"].format(nutrition=entities["nutrition_names"][0])
        elif intent == "brand_query" and entities.get("brand_names"):
            return templates["brand_query"].format(brand=entities["brand_names"][0])

        return None

    def _fix_common_cypher_errors(self, cypher):
        """Fix common Cypher errors"""
        # Remove possible Markdown code blocks
        cypher = re.sub(r'```cypher\n?|```\n?', '', cypher)

        # Make sure toLower() is used for string comparisons
        # This is a simple fix, more complex cases may require better parsing
        if 'name =' in cypher and 'toLower(' not in cypher:
            cypher = re.sub(r'name = "([^"]+)"', r'toLower(name) = "\1"', cypher)

        return cypher.strip()

    def generate_robust_cypher(self, question, chat_history=None):
        """Construct a robust Cypher query with validation and fallback"""
        print(f"[DEBUG] Generating Cypher for: {question}")

        # Step 0: Check if chat history is provided
        if chat_history:
            mentioned_products = self.resolve_product_coreference(question, chat_history)
            if mentioned_products:
                product_hint = ", ".join(mentioned_products)
                question = f"User mentioned products:{product_hint}。\nUser question:{question}"

        # Step 1: Generate multiple candidates based on combined questions if chat history is provided
        candidates = self._generate_multiple_candidates(question)
        print(f"[DEBUG] Generated {len(candidates)} candidates")

        best_cypher = None
        best_score = -1
        validation_results = {}

        for i, cypher in enumerate(candidates):
            if not cypher:
                continue

            print(f"[DEBUG] Testing candidate {i + 1}: {cypher[:100]}...")

            # Fix common Cypher errors
            fixed_cypher = self._fix_common_cypher_errors(cypher)

            # Syntax validation
            is_valid, error_msg = self._validate_cypher_syntax(fixed_cypher)
            validation_results[f"candidate_{i + 1}"] = {
                "cypher": fixed_cypher,
                "syntax_valid": is_valid,
                "error": error_msg
            }

            if not is_valid:
                print(f"[DEBUG] Candidate {i + 1} syntax error: {error_msg}")
                continue

            # Execute the Cypher query to test if it runs correctly
            can_execute, result = self._test_cypher_execution(fixed_cypher)
            validation_results[f"candidate_{i + 1}"]["can_execute"] = can_execute
            validation_results[f"candidate_{i + 1}"]["result_preview"] = result if can_execute else str(result)

            if can_execute:
                # Calculate a score based on the result
                score = len(result) if isinstance(result, list) else 1
                print(f"[DEBUG] Candidate {i + 1} score: {score}")

                if score > best_score:
                    best_score = score
                    best_cypher = fixed_cypher
            else:
                print(f"[DEBUG] Candidate {i + 1} execution error: {result}")

        if not best_cypher:
            # All candidates failed, use a fallback query
            print("[DEBUG] All candidates failed, using fallback")
            best_cypher = "MATCH (p:Product) RETURN p.name, p.url LIMIT 10"
            validation_results["fallback"] = {"cypher": best_cypher, "reason": "All candidates failed"}

        return best_cypher, validation_results

    def query_with_fallback(self, question, chat_history):
        """Cypher query with fallback mechanism"""
        try:
            # Step 1: Generate robust Cypher query
            cypher_query, validation_info = self.generate_robust_cypher(question, chat_history)
            print(f"[DEBUG] Selected Cypher: {cypher_query}")

            # Step 2: Execute the Cypher query
            with self.driver.session() as session:
                result = session.run(cypher_query)
                data = result.data()

                if not data:
                    # Use broad fallback if no results
                    fallback_cypher = "MATCH (p:Product) RETURN p.name, p.url, p.category LIMIT 20"
                    result = session.run(fallback_cypher)
                    data = result.data()
                    cypher_query = fallback_cypher

                return {
                    "success": True,
                    "data": data,
                    "cypher_used": cypher_query,
                    "validation_info": validation_info,
                    "result_count": len(data)
                }

        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "cypher_used": cypher_query if 'cypher_query' in locals() else None,
                "validation_info": validation_info if 'validation_info' in locals() else {}
            }

    def resolve_product_coreference(self, question, chat_history):
        def build_prompt(q, history):
            history_text = "\n".join([f"{item['sender']}: {item['text']}" for item in history])
            return f"""You're an intelligent assistant, and you're asked to determine, based on a user's history of conversations, which product they're referring to when they mention pronouns like “it”, “this”, "first one", "last one", "them", "th one" in their latest question.

                    Conversation history:
                    {history_text}
                
                    Latest question from user:
                    "{q}"
                
                    Please return only a list of the product name mentioned, no extra explanation or additional description is needed, if no specific product is mentioned, then return "None".
                    """

        prompt = build_prompt(question, chat_history)
        response = self.llm([HumanMessage(content=prompt)])
        answer = response.content.strip()
        if answer.lower() == "none":
            return None
        return answer.split(", ")

def grag_view(question, chat_history):
    if not question:
        return Response({"error": "Missing question."}, status=400)

    # Initialize the enhanced GraphRAG
    enhanced_rag = EnhancedGraphRAG()

    try:
        # Utilize the enhanced query method
        query_result = enhanced_rag.query_with_fallback(question, chat_history)

        if not query_result["success"]:
            return Response({
                "error": query_result["error"],
                "debug_info": query_result.get("validation_info", {})
            }, status=500)

        # Retrieve the results
        cypher_answer = query_result["data"]
        cypher_query = query_result["cypher_used"]

        print(f"[DEBUG] Query successful. Found {query_result['result_count']} results")
        print(f"[DEBUG] Used Cypher: {cypher_query}")

        # Return error message if no results found
        if not cypher_answer:
            return Response({
                "answer": "I couldn't find any relevant information in our database for your question. Could you try rephrasing or asking about specific products or nutrition information?",
                "debug_info": {
                    "cypher_used": cypher_query,
                    "result_count": 0
                }
            }, status=200)

        # Generate the final response using the LLM
        system_prompt = """
                        Your home website is https://www.madewithnestle.ca/ and you must only use the provided context to answer the question.
                        Do not rely on your own knowledge or assumptions.
                        If the user asks for your name, respond with: "My name is Nestle Assistant, I'm your personal MadeWithNestle assistant."
                        Be concise, factual, and in English. **Do not say 'based on the context'**.
                        Only use content that is clearly relevant to the question.
                        Ignore irrelevant products or content even if they are nearby in the context.
                        
                        If the answer contains product recommendations, format each product as a markdown hyperlink: [**Product Name**](product_url)
                        """

        user_prompt = f"""
                        User asked: {question}
                
                        Results from Neo4j graph database:
                        {json.dumps(cypher_answer, indent=2)}
                
                        Respond conversationally like a helpful assistant. Use appropriate emojis when suitable.
                        Focus on the most relevant results and present them clearly.
                        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        final_response = enhanced_rag.llm.invoke(messages)

        return Response({
            "answer": final_response.content,
            "debug_info": {
                "cypher_used": cypher_query,
                "result_count": query_result["result_count"],
                "validation_info": query_result.get("validation_info", {})
            }
        }, status=200)

    except Exception as e:
        print(f"[ERROR] Enhanced GraphRAG failed: {e}")

        # LAST RESORT: Fallback to original method
        try:
            print("[DEBUG] Falling back to original method")

            llm = AzureChatOpenAI(
                openai_api_type="azure",
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                temperature=0,
                n=1
            )

            graph = Neo4jGraph(
                url=os.getenv("NEO4J_URI"),
                username=os.getenv("NEO4J_USERNAME"),
                password=os.getenv("NEO4J_PASSWORD")
            )

            # Construct the basic Cypher chain
            cypher_chain = GraphCypherQAChain.from_llm(
                llm=llm,
                graph=graph,
                verbose=True,
                return_intermediate_steps=True,
                allow_dangerous_requests=True
            )

            result = cypher_chain.invoke(question)
            return Response({"answer": result["result"]}, status=200)

        except Exception as fallback_error:
            print(f"[ERROR] Fallback also failed: {fallback_error}")
            return Response({
                "error": "I'm having trouble processing your question right now. Please try again later.",
                "debug_error": str(e)
            }, status=500)
