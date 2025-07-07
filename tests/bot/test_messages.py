# tests/bot/test_messages.py
import time
import pytest
from qr_auth.models import Room, User  # qr_auth.User ni import qilamiz
from datetime import date
from channels.db import database_sync_to_async

# Sozlamalarni yuklashni ta'minlash
import django
django.setup()

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_handle_message_success(mocker):
    room = await database_sync_to_async(Room.objects.create)(
        number=f"101_{int(time.time())}",  # Unik raqam
        check_in=date(2024, 1, 1),
        check_out=date(2024, 1, 10),
        is_active=True
    )
    username = f"test_staff_{int(time.time())}"
    user = await database_sync_to_async(User.objects.create)(
        username=username,
        email=f"{username}@example.com",
        telegram_id=f"tg_{int(time.time())}",  # telegram_id qo'shamiz
        phone="1234567890",  # phone maydonini to'ldiramiz
        is_active=True
    )
    await database_sync_to_async(user.set_password)("testpass123")
    await database_sync_to_async(user.save)()
    assert user.is_active is True