import logging
import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async

from ..notification.services import create_notification

logger = logging.getLogger(__name__)


def broadcast_chat_message(message):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.info("No channel layer found, closing task")
        return 
    room_id = message.conversation.conversation_id
    id = str(room_id)
    async_to_sync(channel_layer.group_send)(
        f"chat_group_{id}", 
        {
            'type': "chat_message",
            "message_id": str(message.pk),
            "sender_display_name": message.sender.profile.display_name,
            "conversation_id": id,
            "message": message.content,
            'created_at': str(message.created_at)
        }
    )

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

    async def chat_message(self, event):
        logger.info("broadcasting message to websocket")


        await self.send(text_data= json.dumps({
            "type": "message_sent",
            "message_id": event['message_id'],
            "sender": event['sender_display_name'],
            "conversation_id": event['conversation_id'],
            "message": event['message'],
            'created_at': event['created_at']
        }))

    @database_sync_to_async
    def save_notifications(self, sender_id, receiver_id, event, message):
        return create_notification(event=event, message=message, sender=sender_id, receiver=receiver_id)

        