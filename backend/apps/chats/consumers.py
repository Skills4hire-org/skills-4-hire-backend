import logging
import json


from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


from ..notification.services import create_notification
from .models import Message, Conversation
from ..core.utils.py import get_or_none
from ..authentication.serializers import UserReadSerializer
from .serializers import MessageListSerializer

from django.utils import timezone
from django.contrib.auth import get_user_model
from enum import Enum
from types import SimpleNamespace

logger = logging.getLogger(__name__)
UserModel = get_user_model()


class Event(str, Enum):
    TYPING = "typing"
    MESSAGE = "message"
    PING = "ping"

class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        if not self.room_id:
            logger.info("Room Id is not present to accept websocket connection")
            await self.close()
            return 
        conversation = await self.get_conversation(self.room_id)
        if conversation is None:
            logger.info(f"Error fetching conversation: {conversation}")
            await self.send_json(content={"error": False, 'message': "Failed to fetch conversation"})
            await self.close()
            return

        self.auth_user = self.scope.get('user')
        if self.auth_user is None or self.auth_user.is_anonymous:
            logger.info("User not found")
            await self.close(code=4003)

        self.is_participant = await database_sync_to_async(conversation.has_participant)(self.auth_user)
        if not self.is_participant:
            logger.info("User is not a participant of this conversation")
            await self.close(code=4003)

        self.group_name = f"chat_group_{self.room_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        event = content.get("event")
        handlers = {
            Event.TYPING: self.handle_typing,
            Event.PING: self.handle_ping,
            Event.MESSAGE: self.handle_chat_message
        }
        handler = handlers.get(event)
        if handler:
            await handler(content)
        else:
            await self.send_json(content={'event': "error", "message": f"Invalid event type {event}"})

    async def handle_ping(self, data):
        await self.send_json(content={"type": "pong"})

    async def handle_typing(self, data):
        user_id = data.get("user_id")
        user = await self.user(user_id)
        user_data = await self.serializer_data(UserReadSerializer, user)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': "user_typing",
                "event": Event.TYPING,
                "user_data": user_data,
            }
        )

    async def user_typing(self, content):
        logger.info("broadcasting user typing")

        await self.send_json(content={
            "event": content.get("event"),
            "user_data": content.get("user_data"),
            "typing": True,
            "server_time": timezone.now().isoformat()
        })

    async def handle_chat_message(self, data):
        message_id = data.get("message_id")

        message = await self.get_message(message_id)
        message_data = await self.serializer_data(MessageListSerializer, message)
        await self.channel_layer.group_send(
            self.group_name, 
            {
                'type': "chat_message",
                'message': message_data
            }
        )

    async def chat_message(self, content):
        logger.info("broadcasting message")
        await self.send_json(content={
            "event": Event.MESSAGE,
            "message": content.get("message", None),
            "server_timestamp": timezone.now().isoformat()
        })


    @database_sync_to_async
    def serializer_data(self, serializer_class, instance):
        user = self.scope.get("user")
        request = SimpleNamespace(user=user)
        serializer = serializer_class(instance, context={'request': request})
        return serializer.data

    
    @database_sync_to_async
    def user(self, user_id):
        user = UserModel.objects.filter(pk=user_id, is_active=True).first()
        return user


    @database_sync_to_async
    def get_conversation(self, conversation_id):
        conversation = get_or_none(Conversation, conversation_id=conversation_id)
        return conversation
    
    @database_sync_to_async
    def save_notifications(self, sender_id, receiver_id, event, message):
        return create_notification(event=event, message=message, sender=sender_id, receiver=receiver_id)

    @database_sync_to_async
    def get_message(self, message_id):
        return get_or_none(Message, pk=message_id, is_active=True)
        