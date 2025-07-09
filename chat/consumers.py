import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_number = self.scope['url_route']['kwargs']['room_number']
        self.group_name  = f"chat_{self.room_number}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data   = json.loads(text_data)
        msg    = data.get('message')
        sender = data.get('sender', 'me')
        if not msg:
            return

        await self.channel_layer.group_send(self.group_name, {
            "type": "chat.message",
            "message": msg,
            "sender": sender,
            "time": timezone.now().strftime('%H:%M')
        })

    async def chat_message(self, event):
        # front‑endga faqat bitta nusxa ketadi
        await self.send(text_data=json.dumps(event))
