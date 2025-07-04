from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from qr_auth.models import Room
from .models import Message
from .serializers import MessageSerializer

class MessageListView(APIView):
    def get(self, request, room_number):
        try:
            room = Room.objects.get(number=room_number)
            messages = Message.objects.filter(chatroom=room)
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Room.DoesNotExist:
            return Response({"error": "Xona topilmadi"}, status=status.HTTP_404_NOT_FOUND)

class MessageCreateView(APIView):
    def post(self, request, room_number):
        try:
            room = Room.objects.get(number=room_number)
            serializer = MessageSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(chatroom=room)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Room.DoesNotExist:
            return Response({"error": "Xona topilmadi"}, status=status.HTTP_404_NOT_FOUND)

def chat_view(request, room_number):
    return render(request, 'chat/index.html', {'room_number': room_number})