# chat/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from qr_auth.models import Room
from chat.models import Message
from datetime import date

class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.room = Room.objects.create(
            number="101",
            check_in=date(2024, 1, 1),
            check_out=date(2024, 1, 10),
            is_active=True
        )

    def test_get_messages(self):
        Message.objects.create(chatroom=self.room, text="Test", is_from_customer=True)
        response = self.client.get("/api/messages/101/", SERVER_NAME='localhost:8004')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['text'], "Test")

    def test_send_message(self):
        response = self.client.post(
            "/api/messages/101/send/",
            {'text': 'Test', 'is_from_customer': False},
            format='json',
            SERVER_NAME='localhost:8004'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.objects.count(), 1)