#chat/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from qr_auth.models import Room
from chat.models import Message
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .utils import enqueue_if_offline
import uuid

@api_view(['POST'])
def send_message(request, room_number):
    text = request.data.get('text')
    uuid_val = request.data.get('uuid')
    if not text or not uuid_val:
        return Response({'error': 'text & uuid required'}, status=400)

    room, _ = Room.objects.get_or_create(number=room_number)

    # Bazaga saqlaymiz
    Message.objects.create(
        chatroom=room,
        text=text,
        uuid=uuid_val,
        is_from_customer=True,
        status="delivered"
    )

    group_name = f"chat_{room_number}"
    channel_layer = get_channel_layer()

    # Hozirgi barcha WebSocket clientlar
    is_anyone_online = async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'chat_message',
            'message': text,
            'sender': 'me',
            'time': timezone.now().strftime('%H:%M'),
            'uuid': uuid_val,
        }
    )

    # ❗ is_anyone_online ni tekshirish iloji yo‘q → biz har doim yozamiz
    enqueue_if_offline(room_number, text, uuid_val, sender='me')

    return Response({'status': 'delivered'})

@api_view(['GET'])
def get_message_history(request, room_number):
    msgs = Message.objects.filter(chatroom__number=room_number).order_by('sent_at')
    from rest_framework import serializers
    class Ser(serializers.ModelSerializer):
        class Meta:
            model = Message
            fields = ['text', 'sent_at', 'is_from_customer', 'uuid']
    return Response(Ser(msgs, many=True).data)

@api_view(['GET'])
def rooms_list(request):
    rooms = Room.objects.all().values_list('number', flat=True)
    return Response(list(rooms))


