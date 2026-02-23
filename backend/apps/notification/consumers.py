from channels.generic.websocket import AsyncWebsocketConsumer

import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = f"user_{self.scope['user'].pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
    
    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notifications(self, data):
        await self.send(text_data=json.dumps({
            "message": data["message"]
        }))
        