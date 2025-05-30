from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_MODEL_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# 2. Initialize the Azure OpenAI client
llm = AzureChatOpenAI(
    openai_api_type="azure",
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_OPENAI_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_deployment=AZURE_OPENAI_MODEL_DEPLOYMENT,
    temperature=0.0,
    max_tokens=20
)

# 3. Match product with LLM
def product_match(question, product_keywords):
    prompt = f"""
                You are an intelligent product name matching assistant.
                Please find the product that best matches the question entered by the user in the following list of product names, returning only the name of the best product and nothing else. Return None if you can't find it.
                
                Product and brand names:
                {chr(10).join(product_keywords)}
                User Input: {question}
                Matched Name:
            """
    messages = [
        SystemMessage(content="You are an intelligent product name matching assistant that can only return the most matching product name in the list."),
        HumanMessage(content=prompt)
    ]
    response = llm(messages)
    answer = response.content.strip()
    # Starndardize the answer to lowercase and remove special quotes
    if answer.lower() == "none":
        return None
    # Double check if the answer is in the product list
    norm_ans = answer.lower().replace("’", "'").replace("‘", "'")
    valid_choices = [x.lower().replace("’", "'").replace("‘", "'") for x in product_keywords]
    if norm_ans in valid_choices:
        # Return the original product name from the list
        idx = valid_choices.index(norm_ans)
        return [product_keywords[idx]]
    return None


# TEST CASE
if __name__ == "__main__":
    test_cases = [
        "Where can I find aero?",
        "can i have kit kat",
        "I want kitkat",
        "Do you have smores?",
        "Looking for s'mores",
        "coffee crisp",
        "afterweight",
        "bigurk",
        "I want something with coffee",
        "I want aero smores"
    ]
    # for q in test_cases:
        # matched = product_match(q, product_keywords)
        # print(f"Query: '{q}' -> Matched: {matched}")
