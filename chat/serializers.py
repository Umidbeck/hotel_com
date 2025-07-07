# chat/serializers.py
from rest_framework import serializers
from .models import Message
from qr_auth.models import Room

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['chatroom', 'text', 'sent_at', 'is_from_customer']
        read_only_fields = ['chatroom', 'sent_at']