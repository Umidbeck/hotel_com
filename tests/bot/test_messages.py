# tests/bot/test_messages.py
import time
import pytest
from django.contrib.auth.models import User
from qr_auth.models import Room
from datetime import date
from channels.db import database_sync_to_async

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_handle_message_success(mocker):
    room = await database_sync_to_async(Room.objects.create)(
        number="101",
        check_in=date(2024, 1, 1),
        check_out=date(2024, 1, 10),
        is_active=True
    )
    username = f"test_staff_{int(time.time())}"
    user = await database_sync_to_async(User.objects.create)(
        username=username,
        email=f"{username}@example.com",
        is_active=True
    )
    await database_sync_to_async(user.set_password)("testpass123")
    await database_sync_to_async(user.save)()
    assert user.is_active is True