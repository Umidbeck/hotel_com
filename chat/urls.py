from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('messages/<str:room_number>/', views.MessageListView.as_view(), name='message_list'),
    path('messages/<str:room_number>/send/', views.MessageCreateView.as_view(), name='message_create'),
    path('chat/<str:room_number>/', views.chat_view, name='chat_view'),
]