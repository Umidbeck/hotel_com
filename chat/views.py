from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from qr_auth.models import Room
from .models import Message
from .serializers import MessageSerializer
from .utils import enqueue_if_offline

@api_view(['POST'])
def send_message(request, room_number):
    text = request.data.get('text')
    is_from_customer = request.data.get('is_from_customer', True)
    uuid_value = request.data.get('uuid')

    if not text or not uuid_value:
        return Response({'error': 'Text yoki UUID kerak'}, status=400)

    try:
        room = Room.objects.get(number=room_number)
    except Room.DoesNotExist:
        return Response({'error': 'Xona topilmadi'}, status=404)

    # duplicate oldini olish
    if Message.objects.filter(uuid=uuid_value).exists():
        return Response({'status': 'duplicate'}, status=200)

    # saqlash
    msg = Message.objects.create(
        chatroom=room,
        text=text,
        uuid=uuid_value,
        is_from_customer=is_from_customer
    )

    # WebSocketga yuborish
    channel_layer = get_channel_layer()
    success = async_to_sync(channel_layer.group_send)(
        f"chat_{room_number}",
        {
            'type': 'chat_message',
            'message': text,
            'sender': 'bot' if not is_from_customer else 'me',
            'time': msg.sent_at.strftime('%H:%M'),
            'uuid': str(uuid_value)
        }
    )

    if not success:
        enqueue_if_offline(room_number, text, uuid_value)

    return Response({'status': 'delivered' if success else 'pending'}, status=201)

@api_view(['GET'])
def get_message_history(request, room_number):
    msgs = Message.objects.filter(chatroom__number=room_number).order_by('sent_at')
    serializer = MessageSerializer(msgs, many=True)
    return Response(serializer.data)

