#chat/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from qr_auth.models import Room
from . import serializers
from .models import Message
from rest_framework import serializers
from .utils import enqueue_if_offline

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['text', 'sent_at', 'is_from_customer', 'uuid']

@api_view(['POST'])
def send_message(request, room_number):
    text = request.data.get('text')
    uuid_val = request.data.get('uuid')
    if not text or not uuid_val:
        return Response({'error': 'text & uuid required'}, status=400)
    try:
        room = Room.objects.get(number=room_number)
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=404)
    if Message.objects.filter(uuid=uuid_val).exists():
        return Response({'status': 'duplicate'}, status=200)
    Message.objects.create(
        chatroom=room,
        text=text,
        uuid=uuid_val,
        is_from_customer=True,
        status="delivered"
    )
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{room_number}",
        {
            'type': 'chat_message',
            'message': text,
            'sender': 'me',
            'time': timezone.now().strftime('%H:%M'),
            'uuid': uuid_val,
        }
    )
    return Response({'status': 'delivered'})

@api_view(['GET'])
def get_message_history(request, room_number):
    msgs = Message.objects.filter(chatroom__number=room_number).order_by('sent_at')
    return Response(MessageSerializer(msgs, many=True).data)


@api_view(['GET'])
def rooms_list(request):
    rooms = Room.objects.all().values_list('number', flat=True)
    return Response(list(rooms))

