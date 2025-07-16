from django.contrib import admin
from .models import Room, User

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'telegram_chat_id',
        'token',
        'language'
    )
    list_editable = ('telegram_chat_id',)
    search_fields = ('number',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'telegram_id', 'phone')
