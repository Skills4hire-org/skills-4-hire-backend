from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async



class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        UserModel = get_user_model()
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]

        print(self.user_id)
        # if not await database_sync_to_async(UserModel.objects.filter(pk=self.user_id).exists)():
        #     await self.close()
        #     return
        
        self.group_name = f"user_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notifications(self, data):
        await self.send(text_data=json.dumps({
            "message": data["message"]
        }))