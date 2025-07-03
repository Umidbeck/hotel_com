# chat/admin.py
from django.contrib import admin
from .models import ChatRoom

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'staff', 'is_active')
    search_fields = ('room_number',)