from django.contrib import admin
from django.urls import path
from chatbot.views import ChatbotView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/chat/', ChatbotView.as_view()),
]
