from .consumers import ChatConsumer
from django.urls import path


chats_urlpatterns = [
    path("ws/chats/<str:room_id>/", ChatConsumer.as_asgi(), name='chat-websocket')
]