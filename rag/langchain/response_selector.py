import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

def question_classifier(question):
    system_prompt = """You are a smart assistant that classifies user questions into one of three categories:
                        1. "store" - if the question is about finding where to buy a product or locating nearby stores.
                        2. "graphrag" - if the question is about structured product information like nutrition facts, features, category, ingredients, or asking 'how many'/'how much'.
                        3. "rag" - if the question is general, like asking about a product's description or brand info.

                        Respond ONLY with one of the following exact words: "store", "graphrag", or "rag".
                    """

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0,
        max_tokens=10,
    )

    classification = response.choices[0].message.content.strip().lower()
    if classification not in ["store", "graphrag", "rag"]:
        return "rag"
    return classification


if __name__ == "__main__":
    question = input("Please enter your question: ")
    while question != "exit":
        result = question_classifier(question)
        print(result)
        question = input("Please enter your question: ")