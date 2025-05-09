from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

class ChatbotView(APIView):
    def post(self, request):
        user_message = request.data.get('message', '')
        # 这里可以接入规则或OpenAI等模型
        bot_reply = f"你说的是：{user_message}，我还不太懂。"
        return Response({'reply': bot_reply})
