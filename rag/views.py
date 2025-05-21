import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from rag.langchain.rag_answer import query_with_langchain_rag
# from .preprocessing.query_with_rag import query_with_rag


@api_view(["POST"])
def rag_ask_view(request):
    question = request.data.get("question")
    name = request.data.get("name")
    if not question:
        return Response({"error": "Missing question"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # answer = query_with_rag(question, chatbot_name=name)
        answer = query_with_langchain_rag(question, chatbot_name=name)
        return Response(answer)
    except Exception as e:
        print("[ERROR]", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
