# hotel/chat/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from chat.models import Message
from qr_auth.models import Room
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.utils import timezone
from telegram import Bot
from decouple import config
import asyncio

@api_view(['POST'])
@permission_classes([AllowAny])
async def send_message(request, room_number):
    try:
        text = request.data.get("text")
        is_from_customer = request.data.get("is_from_customer", True)

        room = await sync_to_async(Room.objects.get)(number=room_number)
        chat_id = room.telegram_chat_id

        # Bazaga yozish
        msg = await sync_to_async(Message.objects.create)(
            chatroom=room,
            text=text,
            is_from_customer=is_from_customer
        )

        # WebSocket orqali xabar jo'natish
        channel_layer = get_channel_layer()
        await channel_layer.group_send(f"chat_{room_number}", {
            "type": "chat_message",
            "message": text,
            "sender": "me" if is_from_customer else "bot",
            "time": timezone.now().strftime("%H:%M")
        })

        # Telegramga xabar jo'natish (agar mijozdan bo‘lsa)
        if is_from_customer and chat_id:
            bot = Bot(token=config("BOT_TOKEN"))
            await bot.send_message(chat_id=chat_id, text=text)

        return Response({"status": "success"}, status=201)
    except Room.DoesNotExist:
        return Response({"error": "Xona topilmadi"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)