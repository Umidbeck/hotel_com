# tests/bot/test_commands.py
import pytest
from channels.db import database_sync_to_async
from django.test import TestCase
from unittest.mock import AsyncMock, patch
from telegram import Update, Message, Chat
from telegram.ext import ContextTypes
from bot.bot import start, messages, reply
from qr_auth.models import Room
from chat.models import Message
from datetime import date
from rest_framework.test import APIClient

@pytest.mark.asyncio
@pytest.mark.django_db
class TestBotCommands(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            number="101",
            check_in=date(2024, 1, 1),
            check_out=date(2024, 1, 10),
            is_active=True
        )
        self.client = APIClient()
        self.update = AsyncMock(spec=Update)
        self.update.message = AsyncMock(spec=Message)
        self.update.message.chat = AsyncMock(spec=Chat)
        self.update.message.chat_id = 12345  # To‘g‘ri mock
        self.context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
        self.context.bot.send_message = AsyncMock()

    async def test_start_command(self):
        await start(self.update, self.context)
        self.context.bot.send_message.assert_called_with(
            chat_id=12345,
            text="Xush kelibsiz! /messages bilan xabarlarni ko‘ring."
        )

    async def test_messages_command(self):
        await database_sync_to_async(Message.objects.create)(
            chatroom=self.room,
            text="Test xabar",
            is_from_customer=True
        )
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[
                {"chatroom": "101", "text": "Test xabar", "is_from_customer": True}
            ])
            mock_get.return_value.__aenter__.return_value = mock_response

            await messages(self.update, self.context)
            self.context.bot.send_message.assert_called_with(
                chat_id=12345,
                text="101: Test xabar"
            )

    async def test_messages_command_no_messages(self):
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.json = AsyncMock(return_value={"error": "Xona topilmadi"})
            mock_get.return_value.__aenter__.return_value = mock_response

            await messages(self.update, self.context)
            self.context.bot.send_message.assert_called_with(
                chat_id=12345,
                text="Xabarlar topilmadi."
            )

    async def test_reply_command(self):
        self.update.message.text = "Javob xabari"
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value={
                "chatroom": "101",
                "text": "Javob xabari",
                "is_from_customer": False
            })
            mock_post.return_value.__aenter__.return_value = mock_response

            await reply(self.update, self.context)
            self.context.bot.send_message.assert_called_with(
                chat_id=12345,
                text="Javob yuborildi."
            )
            mock_post.assert_called_with(
                "http://localhost:8000/api/messages/101/send/",
                json={'text': "Javob xabari", 'is_from_customer': False}
            )

    async def test_reply_command_error(self):
        self.update.message.text = "Javob xabari"
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.json = AsyncMock(return_value={"error": "Xona topilmadi"})
            mock_post.return_value.__aenter__.return_value = mock_response

            await reply(self.update, self.context)
            self.context.bot.send_message.assert_called_with(
                chat_id=12345,
                text="Xato yuz berdi."
            )