from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from rag.langchain.rag_answer import query_with_langchain_rag
from rag.langchain.graph_answer import grag_view
from geolocation.location_finder import location_query
from rag.langchain.response_selector import question_classifier

@api_view(["POST"])
def rag_ask_view(request):
    question = request.data.get("question").lower()
    name = request.data.get("name")
    lat = request.data.get('latitude')
    lon = request.data.get('longitude')
    chat_history = request.data.get("chat_history", [])

    print("[DEBUG] history:", chat_history)

    if not question:
        return Response({"error": "Missing question"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        option = question_classifier(question)
        # Find store locator and provide Amazon link
        if option == "store":
            answer = location_query(question, float(lon), float(lat), chat_history)
            return answer
        # If the question is about nutrition facts or how many/much of a specific nutrition (GraphRAG)
        elif option == "graphrag":
            answer = grag_view(question, chat_history)
            return answer
        # If the question is about a specific product or brand (LangChain RAG)
        else:
            answer = query_with_langchain_rag(question, chatbot_name=name, chat_history=chat_history)
            return Response(answer)
    except Exception as e:
        print("[ERROR]", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
