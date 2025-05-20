import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rag.langchain.rag_answer import query_with_langchain_rag
from .preprocessing.query_with_rag import query_with_rag


@csrf_exempt
def rag_ask_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        question = data.get("question")
        name = data.get("name")
        if not question:
            return JsonResponse({"error": "Missing question"}, status=400)

        try:
            # answer = query_with_rag(question, chatbot_name=name)
            answer = query_with_langchain_rag(question, chatbot_name=name)
            return JsonResponse(answer)
        except Exception as e:
            print("[ERROR]", e)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)
