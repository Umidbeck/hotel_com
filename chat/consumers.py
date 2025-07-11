import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import Message
from qr_auth.models import Room


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_number = self.scope['url_route']['kwargs']['room_number']
        self.group_name = f"chat_{self.room_number}"  # Guruh nomi

        # WebSocket kanalini guruhga qo‘shish
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print(f"[✅ CONNECT] Room: {self.room_number}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"[❌ DISCONNECT] Room: {self.room_number}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message')
            uuid = data.get('uuid')

            if not message or not uuid:
                print("[⚠️ Ogohlantirish] Xabar yoki UUID yo‘q")
                return

            # Agar allaqachon shu uuid bilan xabar yozilgan bo‘lsa → qaytamiz
            if await self.message_exists(uuid):
                print(f"[ℹ️ Duplicate] Xabar allaqachon bor. UUID: {uuid}")
                return

            # Bazaga yozish
            room = await self.get_room(self.room_number)
            msg = await self.save_message(room, message, uuid)

            # Boshqalarga yuborish
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'message': msg.text,
                    'sender': 'me',
                    'time': msg.sent_at.strftime('%H:%M'),
                    'uuid': str(msg.uuid)
                }
            )

            print(f"[✅ Yuborildi] Room: {self.room_number} | UUID: {uuid}")

        except Exception as e:
            print(f"[❌ Xatolik receive()] {e}")

    async def chat_message(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            print(f"[❌ Xatolik send()] {e}")

    # ------------------------
    # 🧠 ORM chaqiruvlari
    # ------------------------

    @database_sync_to_async
    def get_room(self, number):
        return Room.objects.get(number=number)

    @database_sync_to_async
    def save_message(self, room, text, uuid):
        return Message.objects.create(
            chatroom=room,
            text=text,
            uuid=uuid,
            is_from_customer=True
        )

    @database_sync_to_async
    def message_exists(self, uuid):
        return Message.objects.filter(uuid=uuid).exists()




