from django.urls import path
from rag.views import rag_ask_view
from rag.langchain.combine_answer import grag_view

urlpatterns = [
    # path('chat/', chat_view),
    path("chat/", rag_ask_view),
    path("gchat/", grag_view)
]