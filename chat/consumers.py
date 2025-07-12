import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Message
from qr_auth.models import Room
import uuid as uuid_lib

def clean_room(raw: str) -> str:
    return re.sub(r'^-100', 'g', raw)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        raw = self.scope['url_route']['kwargs']['room_number']
        self.room_number = clean_room(raw)
        self.group_name = f"chat_{self.room_number}"

        # Xona mavjudligini tekshirish
        self.room = await database_sync_to_async(
            Room.objects.filter(number=self.room_number).first
        )()

        if not self.room:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get('message')
        uuid_str = data.get('uuid')
        sender = data.get('sender', 'me')

        if not message_text or not uuid_str or not self.room:
            return

        # duplicate oldini olish + status yangilash
        msg, created = await database_sync_to_async(Message.objects.get_or_create)(
            chatroom=self.room,
            uuid=uuid_str,
            defaults={
                "text": message_text,
                "is_from_customer": sender == 'me',
                "status": "delivered",
            }
        )
        if not created:
            return  # duplicate xabar

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": message_text,
                "sender": sender,
                "time": timezone.now().strftime("%H:%M"),
                "uuid": uuid_str,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))