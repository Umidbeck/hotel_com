#qr_auth/models.py
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    telegram_id = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        swappable = 'AUTH_USER_MODEL'


class Room(models.Model):
    number = models.CharField(max_length=10, unique=True)
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True)
    token = models.CharField(max_length=64, unique=True, blank=True, null=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex  # 32 xarfdan iborat
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"http://localhost:3000/chat/{self.number}?token={self.token}"
