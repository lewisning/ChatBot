from django.urls import path
from chatbot.views import chat_view
from rag.views import rag_ask_view
# from graph.

urlpatterns = [
    # path('chat/', chat_view),
    path("chat/", rag_ask_view),
    # path("graph_chat",)
]