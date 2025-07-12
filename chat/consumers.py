import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .utils import flush_pending

from .models import Message
from qr_auth.models import Room

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_number = self.scope['url_route']['kwargs']['room_number']
        self.group_name = f"chat_{self.room_number}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await database_sync_to_async(flush_pending)(self.room_number)
        print(f"[✅ CONNECT + FLUSH] Room: {self.room_number}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        uuid_str = data.get('uuid')
        sender = data.get('sender', 'me')

        if not message or not uuid_str:
            return

        # room_numberni to‘g‘ri olish
        room = await database_sync_to_async(Room.objects.get)(number=self.room_number)

        # duplicate tekshirish
        exists = await database_sync_to_async(Message.objects.filter(uuid=uuid_str).exists)()
        if exists:
            return

        # saqlash
        await database_sync_to_async(Message.objects.create)(
            chatroom=room,
            text=message,
            uuid=uuid_str,
            is_from_customer=sender == 'me'
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
                'time': timezone.now().strftime('%H:%M'),
                'uuid': uuid_str,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))



