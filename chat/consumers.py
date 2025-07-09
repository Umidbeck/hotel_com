import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_number = self.scope['url_route']['kwargs']['room_number']
        self.group_name = f"chat_{self.room_number}"

        # Qo‘shilish
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"[WS] {self.room_number} xonasi uchun ulanildi")

    async def disconnect(self, close_code):
        # Guruhdan chiqish
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"[WS] {self.room_number} xonasi uzildi")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message')
            sender = data.get('sender', 'me')

            if not message:
                return

            # Guruhga yuborish (Telegramga ham ketadi)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.message',
                    'message': message,
                    'sender': sender,
                    'time': timezone.now().strftime('%H:%M'),
                }
            )

        except Exception as e:
            print(f"[receive xato] {e}")

    async def chat_message(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            print(f"[send xato] {e}")
