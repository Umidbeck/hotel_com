# chat/urls.py

from django.urls import path
from .views import send_message

urlpatterns = [
    path('api/messages/<str:room_number>/send/', send_message),
]