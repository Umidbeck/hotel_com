from django.urls import path
from .views import get_messages, send_message

urlpatterns = [
    path('api/messages/<str:room_number>/', get_messages, name='get_messages'),
    path('api/messages/<str:room_number>/send/', send_message, name='send_message'),
]