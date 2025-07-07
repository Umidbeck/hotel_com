# tests/bot/test_models.py
import time
from datetime import date
from django.test import TestCase
from qr_auth.models import Room
from chat.models import ChatRoom, Message

class RoomTests(TestCase):  # ChatRoomTests → RoomTests
    def setUp(self):
        self.room = Room.objects.create(
            number=f"101_{int(time.time())}",  # Unik raqam
            check_in=date(2024, 1, 1),
            check_out=date(2024, 1, 10),
            is_active=True
        )

    def test_room_str(self):  # test_chatroom_str → test_room_str
        self.assertEqual(str(self.room), self.room.number)

class MessageTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            number=f"101_{int(time.time())}",  # Unik raqam
            check_in=date(2024, 1, 1),
            check_out=date(2024, 1, 10),
            is_active=True
        )

    def test_send_message(self):
        message = Message.objects.create(
            chatroom=self.room,
            text="Test message",
            is_from_customer=True
        )
        self.assertEqual(message.text, "Test message")
        self.assertEqual(message.chatroom, self.room)
        self.assertTrue(message.is_from_customer)

class ChatRoomTests(TestCase):  # Yangi test chat.ChatRoom uchun
    def setUp(self):
        self.chat_room = ChatRoom.objects.create(
            room_number=f"101_{int(time.time())}",  # Unik raqam
            is_active=True
        )

    def test_chatroom_str(self):
        self.assertEqual(str(self.chat_room), f"Chat #{self.chat_room.room_number}")