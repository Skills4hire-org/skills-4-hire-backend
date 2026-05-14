import logging
import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def broadcast_chat_message(message):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.info("No channel layer found, closing task")
        return 
    
    room_id = message.conversation.conversation_id
    async_to_sync(channel_layer.group_send)(
        f"chat_group_{room_id}_", 
        {
            'type': "chat_message",
            "message_id": str(message.pk),
            "sender_display_name": message.sender.profile.diplay_name,
            "conversation_id": str(room_id),
            "message": message.content,
            'created_at': message.created_at
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

        self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def chat_message(self, event):
        logger.info("broadcating message to websocket")
        await self.send(text_data= json.loads({
            "type": "message",
            "message_id": event['message_id'],
            "sender": event['sender_display_name'],
            "conversation_id": event['conversation_id'],
            "message": event['message'],
            'created_at': event['message']
        }))

        