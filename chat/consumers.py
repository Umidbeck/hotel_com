from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from qr_auth.models import Room
from chat.models import ChatRoom, Message
import json

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_number = self.scope['url_route']['kwargs']['room_number']
        self.room_group_name = f'chat_{self.room_number}'

        # Guruhga qo'shilish
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Guruhdan chiqish
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = text_data_json.get('sender', 'user')

        # Xabarni ma'lumotlar bazasiga saqlash
        try:
            room = await Room.objects.aget(number=self.room_number)
            await Message.objects.acreate(
                chatroom=room,
                text=message,
                is_from_customer=(sender == 'user')
            )
        except Room.DoesNotExist:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Xona topilmadi'
            }))
            return

        # Guruhga xabar yuborish
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': message,
                'sender': sender
            }
        )

    async def chat_message(self, event):
        # Xabarni WebSocket orqali yuborish
        await self.send(text_data=json.dumps({
            'type': 'chat.message',
            'message': event['message'],
            'sender': event['sender']
        }))