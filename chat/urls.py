#chat/urls.py
from django.urls import path
from .views import send_message, get_message_history, rooms_list

urlpatterns = [
    path('api/messages/<str:room_number>/', get_message_history),
    path('api/messages/<str:room_number>/send/', send_message),
    path('api/rooms/', rooms_list),
]