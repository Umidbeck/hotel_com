#chat/urls.py
from django.urls import path
from .views import send_message, get_message_history

urlpatterns = [
    path('api/messages/<str:room_number>/', get_message_history),  # Tarix uchun GET
    path('api/messages/<str:room_number>/send/', send_message),    # Yuborish uchun POST
]