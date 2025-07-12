# chat/models.py
from django.db import models
from django.contrib.auth import get_user_model

from qr_auth.models import Room
import uuid

User = get_user_model()


class ChatRoom(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat #{self.room_number}"

    async def send_message(self, message):
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"chat_{self.room_number}",
            {
                "type": "chat.message",
                "message": message
            }
        )
class Message(models.Model):
    chatroom = models.ForeignKey(Room, on_delete=models.CASCADE)
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_from_customer = models.BooleanField(default=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # yangi maydonlar
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    retry_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['chatroom', 'status']),
            models.Index(fields=['uuid']),
        ]

    def __str__(self):
        return f"{self.chatroom} – {self.text[:30]}"