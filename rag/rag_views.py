from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from rag.langchain.rag_answer import query_with_langchain_rag
from rag.langchain.graph_answer import grag_view
from geolocation.location_finder import location_query

@api_view(["POST"])
def rag_ask_view(request):
    question = request.data.get("question").lower()
    name = request.data.get("name")
    lat = request.data.get('latitude')
    lon = request.data.get('longitude')
    nutritions = ["calories", "fat", "carbohydrates", "protein", "sugar", "sodium"]

    if not question:
        return Response({"error": "Missing question"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Find store locator and provide Amazon link
        if "where" in question and "buy" in question and lat and lon:
            answer = location_query(question, float(lon), float(lat))
            return answer
        # If the question is about nutrition facts or how many/much of a specific nutrition (GraphRAG)
        elif "how many" in question or "how much" in question or any(nutrition in question for nutrition in nutritions):
            answer = grag_view(question)
            return answer
        # If the question is about a specific product or brand (LangChain RAG)
        else:
            answer = query_with_langchain_rag(question, chatbot_name=name)
            return Response(answer)
    except Exception as e:
        print("[ERROR]", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
