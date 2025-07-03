# tests/bot/test_models.py
from datetime import date

from django.test import TestCase
from qr_auth.models import Room
from chat.models import Message


class ChatRoomTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            number="101",
            check_in=date(2024, 1, 1),
            check_out=date(2024, 1, 10),
            is_active=True
        )

    def test_chatroom_str(self):
        self.assertEqual(str(self.room), "101")

class MessageTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            number="101",
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