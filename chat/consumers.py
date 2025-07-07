import json
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import Message
from django.core.serializers.json import DjangoJSONEncoder

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_number = self.scope['url_route']['kwargs']['room_number']
        self.room_group_name = f'chat_{self.room_number}'
        print(f"Ulanildi: {self.room_group_name}")  # Log qo‘shish

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        print(f"Uzildi: {self.room_group_name}")  # Log qo‘shish
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = text_data_json.get('sender', 'other')
        print(f"Qabul qilingan xabar: {message} (sender: {sender})")  # Log qo‘shish

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event.get('sender', 'other')
        print(f"Jo'natilayotgan xabar: {message} (sender: {sender})")  # Log qo‘shish

        if sender == 'bot':
            await self.send(text_data=json.dumps({
                'message': message.replace('Bot: ', ''),
                'sender': 'other',
                'time': event.get('time', '')
            }, cls=DjangoJSONEncoder))
        else:
            await self.send(text_data=json.dumps({
                'message': message,
                'sender': sender,
                'time': event.get('time', '')
            }, cls=DjangoJSONEncoder))