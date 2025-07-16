#qr_auth/models.py
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    telegram_id = models.CharField(max_length=100, blank=True, null=True)
    phone        = models.CharField(max_length=20, blank=True, null=True)
    class Meta:
        swappable = 'AUTH_USER_MODEL'

class Room(models.Model):
    number            = models.CharField(max_length=10, unique=True)
    telegram_chat_id  = models.CharField(max_length=100, blank=True, null=True)
    token             = models.CharField(max_length=64, unique=True, blank=True, null=False)
    # 👇 DOIMIY QR uchun (hech qachon o‘zgarmaydi)
    qr_code           = models.CharField(max_length=32, unique=True, blank=False, null=False, default=uuid.uuid4().hex)
    language = models.CharField(max_length=10, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    # Token o‘zgarsa ham, redirect joyi o‘zgaradi
    def get_absolute_url(self):
        return f"http://localhost:3000/chat/{self.number}?token={self.token}"

    # Tokenni yangilash (mehmon ketganda)
    def rotate_token(self):
        self.token = uuid.uuid4().hex
        self.save()
