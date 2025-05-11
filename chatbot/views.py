import os
import openai
from dotenv import load_dotenv
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI API Configuration
openai.api_type = "azure"
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")

deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

@api_view(["POST"])
def chat_view(request):
    user_message = request.data.get('message', '')
    if not user_message:
        return Response({"error": "Message is required"}, status=400)

    try:
        response = openai.ChatCompletion.create(
            engine=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant, especially for Nestle and all products "
                                              "on it's website, https://www.madewithnestle.ca/."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=512,
        )
        reply = response.choices[0].message["content"]
        return Response({"reply": reply})
    except Exception as e:
        print("OpenAI error:", e)
        return Response({"error": str(e)}, status=500)
