import logging
import json


from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


from ..notification.services import create_notification
from .models import Message
from ..core.utils.py import get_or_none

from django.utils import timezone
from enum import Enum

logger = logging.getLogger(__name__)

class Event(str, Enum):
    TYPING = "typing"
    MESSAGE = "message"
    PING = "ping"

class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        if not self.room_id:
            logger.info("Room Id is not present to accept websocker connection")
            await self.close()
            return 
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
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': "user_typing",
                "fullname": data.get("fullname", None),
                "user_id": data.get("user_id", None),
                "is_typing": data.get("is_typing", None),
                "event": "typing"
            }
        )

    async def user_typing(self, content):
        logger.info("broadcasting user typing")
        await self.send_json(content={
            "event": content.get("event"),
            "user_id": content.get("user_id"),
            "fullname": content.get("fullname"),
            "is_typing": content.get("is_typing"),
            "server_time": timezone.now().isoformat()
        })

    async def handle_chat_message(self, data):
        message_id = data.get("message_id")
        message = await self.get_message(message_id)
        if message is None:
            logger.info("message is none, closing connection...")
            await self.close(400)
            return 
        await self.channel_layer.group_send(
            self.group_name, 
            {
                'type': "chat_message",
                "message_id": str(message.pk),
                "sender_display_name": message.sender.profile.display_name,
                "conversation_id": id,
                "message": message.content[:20],
                'created_at': str(message.created_at)
            }
        )

    async def chat_message(self, event):
        logger.info("broadcasting message")
        await self.send(text_data= json.dumps({
            "event": "",
            "message_id": event['message_id'],
            "sender": event['sender_display_name'],
            "conversation_id": event['conversation_id'],
            "message": event['message'],
            'created_at': event['created_at'],
            "server_time": timezone.now().isoformat()
        }))

    @database_sync_to_async
    def save_notifications(self, sender_id, receiver_id, event, message):
        return create_notification(event=event, message=message, sender=sender_id, receiver=receiver_id)

    @database_sync_to_async
    def get_message(self, message_id):
        return get_or_none(Message, pk=message_id, is_active=True)
        