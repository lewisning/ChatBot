from django.urls import path
from rag.rag_views import rag_ask_view
from rag.langchain.graph_answer import grag_view
from tts.tts_generate import tts_generate

urlpatterns = [
    # path('chat/', chat_view),
    path("chat/", rag_ask_view),
    path("gchat/", grag_view),
    path("tts/generate/", tts_generate),
    # path('location_query/', LocationQueryView.as_view()),
]