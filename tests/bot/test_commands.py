# tests/bot/test_commands.py
import pytest
from unittest.mock import AsyncMock, patch
from bot.bot import start, messages, reply
from telegram import Update
from telegram.ext import ContextTypes

class TestBotCommands:
    def setup_method(self):
        self.update = AsyncMock()
        self.update.message.chat_id = 12345
        self.context = AsyncMock()

    async def test_start_command(self):
        self.update.message.text = "/start"
        await start(self.update, self.context)
        self.context.bot.send_message.assert_called_with(
            chat_id=12345,
            text="Xush kelibsiz! /messages bilan xabarlarni ko‘ring."
        )

    async def test_messages_command(self):
        self.update.message.text = "/messages"
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
        self.update.message.text = "/messages"
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            await messages(self.update, self.context)
            self.context.bot.send_message.assert_called_with(
                chat_id=12345,
                text="Xabarlar topilmadi."
            )

    @pytest.mark.django_db
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
                "http://localhost:8004/api/messages/101/send/",
                json={'text': "Javob xabari", 'is_from_customer': False}
            )

    async def test_reply_command_error(self):
        self.update.message.text = "Javob xabari"
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_post.return_value.__aenter__.return_value = mock_response
            await reply(self.update, self.context)
            self.context.bot.send_message.assert_called_with(
                chat_id=12345,
                text="Xato yuz berdi."
            )