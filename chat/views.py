# chat/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Message
from .serializers import MessageSerializer
from qr_auth.models import Room

@api_view(['GET'])
@permission_classes([AllowAny])
def get_messages(request, room_number):
    try:
        room = Room.objects.get(number=room_number, is_active=True)
        messages = Message.objects.filter(chatroom=room)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=200)
    except Room.DoesNotExist:
        return Response({'error': 'Xona topilmadi'}, status=404)

@api_view(['POST'])
@permission_classes([AllowAny])
def send_message(request, room_number):
    try:
        room = Room.objects.get(number=room_number, is_active=True)
        serializer = MessageSerializer(data={
            'chatroom': room.id,
            'text': request.data.get('text'),
            'is_from_customer': request.data.get('is_from_customer', False)
        })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    except Room.DoesNotExist:
        return Response({'error': 'Xona topilmadi'}, status=404)