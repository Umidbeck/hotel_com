# chat/serializers.py
from rest_framework import serializers
from chat.models import Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['text', 'sent_at', 'is_from_customer', 'uuid', 'status']