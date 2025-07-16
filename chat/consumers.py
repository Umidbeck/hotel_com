#chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from chat.models import Message
from qr_auth.models import Room
from urllib.parse import parse_qs
from asgiref.sync import sync_to_async
from chat.utils import flush_pending

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_number = self.scope['url_route']['kwargs']['room_number']
        query = parse_qs(self.scope['query_string'].decode())
        token = query.get('token', [None])[0]

        self.room = await database_sync_to_async(
            lambda: Room.objects.filter(number=self.room_number, token=token).first()
        )()
        if not self.room:
            await self.close(code=4001)
            return

        self.group_name = f"chat_{self.room_number}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # 🌟 Brauzer ulangan zahoti Redis’dan pending larni chiqaramiz
        await sync_to_async(flush_pending)(self.room_number)

    async def disconnect(self, code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        text = data.get('message')
        uuid_str = data.get('uuid')
        sender = 'me'
        if not text or not uuid_str:
            return

        await database_sync_to_async(Message.objects.create)(
            chatroom=self.room,
            text=text,
            uuid=uuid_str,
            is_from_customer=(sender == 'me'),
            status="delivered"
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": text,
                "sender": sender,
                "time": timezone.now().strftime("%H:%M"),
                "uuid": uuid_str,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
