import uuid

from .serializers import MessageSerializer


from uuid import UUID
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from qr_auth.models import Room
from .models import Message


@api_view(['POST'])
def send_message(request, room_number):
    text = request.data.get('text')
    is_from_customer = request.data.get('is_from_customer', False)
    uuid_value = request.data.get('uuid')  # ⬅️ frontenddan kelgan uuid

    if not text or not uuid_value:
        return Response({'error': 'Text yoki UUID yetarli emas.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        room = Room.objects.get(number=room_number)
    except Room.DoesNotExist:
        return Response({'error': 'Xona topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

    # Agar aynan shu uuid bilan xabar allaqachon bazaga yozilgan bo‘lsa, takroran yozmaymiz
    from chat.models import Message
    if Message.objects.filter(uuid=uuid_value).exists():
        return Response({'status': 'duplicate', 'message': 'Xabar allaqachon saqlangan.'}, status=200)

    sender = 'me' if is_from_customer else 'bot'
    time_str = timezone.now().strftime('%H:%M')

    # WebSocket orqali yuborish
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{room_number}",
            {
                'type': 'chat_message',
                'message': text,
                'sender': sender,
                'time': time_str,
                'uuid': str(uuid_value)  # 🔥 qo‘shildi
            }
        )
    except Exception as e:
        return Response({'error': f'WebSocket xato: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Bazaga saqlash
    try:
        Message.objects.create(
            chatroom=room,
            text=text,
            uuid=uuid_value,
            is_from_customer=is_from_customer
        )
    except Exception as e:
        print(f"[❌ DB xato]: {e}")
        return Response({'error': 'Bazaga saqlashda xato'}, status=500)

    return Response({'status': 'success'}, status=status.HTTP_201_CREATED)




@api_view(['GET'])
def get_message_history(request, room_number):
    try:
        room = Room.objects.get(number=room_number)
        messages = Message.objects.filter(chatroom=room).order_by('sent_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    except Room.DoesNotExist:
        return Response({'error': 'Xona topilmadi.'}, status=404)

