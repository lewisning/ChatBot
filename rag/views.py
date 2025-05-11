import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .rag_answer import ask_with_context


@csrf_exempt
def rag_ask_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        question = data.get("question")
        name = data.get("name")
        if not question:
            return JsonResponse({"error": "Missing question"}, status=400)

        try:
            answer = ask_with_context(question, chatbot_name=name)
            return JsonResponse({"answer": answer})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)
