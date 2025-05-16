from django.urls import path
from chatbot.views import chat_view
from rag.views import rag_ask_view

urlpatterns = [
    # path('chat/', chat_view),
    path("chat/", rag_ask_view),
]