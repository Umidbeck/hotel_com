# chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # REST API
    path('api/messages/<str:room_number>/',          views.MessageListView.as_view(),   name='message-list'),
    path('api/messages/<str:room_number>/send/',     views.MessageCreateView.as_view(), name='message-create'),

    # HTML chat sahifasi
    path('chat/<str:room_number>/', views.chat_view, name='chat-view'),
]