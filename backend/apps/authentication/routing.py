from django.urls import path
from .consumers import UserConsumer

userpatterns = [
    path("ws/user/<str:user_id>/", UserConsumer.as_asgi(), name='user-websocket')
]