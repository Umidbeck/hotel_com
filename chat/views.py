# chat/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from qr_auth.models import Room
from .models import Message  # Agar Message modeli mavjud bo'lsa
from .serializers import MessageSerializer  # Agar kerak bo‘lsa

@api_view(['POST'])
def send_message(request, room_number):
    text = request.data.get('text')
    is_from_customer = request.data.get('is_from_customer', False)

    if not text:
        return Response({'error': 'Xabar matni kiritilmagan.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        room = Room.objects.get(number=room_number)
    except Room.DoesNotExist:
        return Response({'error': 'Xona topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

    sender = 'me' if is_from_customer else 'bot'
    time_str = timezone.now().strftime('%H:%M')

    # WebSocketga yuboramiz
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{room_number}",
            {
                'type': 'chat_message',
                'message': text,
                'sender': sender,
                'time': time_str
            }
        )
    except Exception as e:
        return Response({'error': f'WebSocket xato: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # (Ixtiyoriy) Bazaga saqlash
    try:
        # Agar Message modeli bor bo‘lsa, bu yerda saqlaymiz
        # Message.objects.create(room=room, text=text, sender=sender, timestamp=timezone.now())
        pass  # Saqlash hozircha majburiy emas
    except Exception as e:
        print(f"[❌ DB xato]: {e}")

    return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
