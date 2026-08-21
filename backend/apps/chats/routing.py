from typing import Any, cast

from django.urls import path

from .consumers import ChatConsumer


chats_urlpatterns = [
    path("ws/chats/<str:room_id>/", ChatConsumer.as_asgi(), name="chat-websocket")
]