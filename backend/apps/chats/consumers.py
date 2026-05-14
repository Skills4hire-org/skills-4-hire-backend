from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Conversation, Message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs'].get('room_id')
        self.is_support_inbox = self.room_id is None

        if self.is_support_inbox:
            self.group_name = 'support_staff'
        else:
            self.group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)