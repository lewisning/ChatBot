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
def product_match(question, product_keywords, chat_history):
    recent_bot_messages = [msg["text"] for msg in reversed(chat_history) if msg["sender"] == "bot"]
    context_text = "\n\n".join(recent_bot_messages[:1])

    prompt = f"""
            You are a helpful assistant that resolves product mentions in user questions based on context.
            
            Here is the chat history:
            {context_text}
            
            Here is the user question:
            "{question}"
            
            From the following list of product and brand names, identify which one is being referred to by the user. If there is no clear match, return None.
            
            Product and brand names:
            {chr(10).join(product_keywords)}
            
            Return only the matched product name, exactly as listed above. Do not include any explanation.
            
            Matched Name:
            """

    messages = [
        SystemMessage(content="You resolve vague product references using context."),
        HumanMessage(content=prompt)
    ]

    response = llm(messages)
    answer = response.content.strip()

    if answer.lower() == "none":
        return None
    norm_ans = answer.lower().replace("’", "'").replace("‘", "'")
    valid_choices = [x.lower().replace("’", "'").replace("‘", "'") for x in product_keywords]
    if norm_ans in valid_choices:
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
