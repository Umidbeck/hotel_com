from django.contrib import admin
from .models import Room, User

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'telegram_chat_id',
        'is_active',
        'check_in',
        'check_out',
    )
    list_editable = ('telegram_chat_id', 'is_active')
    search_fields = ('number',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'telegram_id', 'phone')
