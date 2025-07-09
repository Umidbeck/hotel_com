# qr_auth/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    telegram_id = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        app_label = 'qr_auth'
        swappable = 'AUTH_USER_MODEL'

class Room(models.Model):
    number            = models.CharField(max_length=10, unique=True)
    telegram_chat_id  = models.BigIntegerField(null=True, blank=True)   # 🆕 guruh ID
    is_active         = models.BooleanField(default=True)
    check_in          = models.DateField()
    check_out         = models.DateField()

    def __str__(self):
        return f"{self.number}"


