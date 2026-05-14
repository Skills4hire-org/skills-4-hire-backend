from channels.generic.websocket import AsyncJsonWebsocketConsumer
import logging 

logger = logging.getLogger(__name__)

class UserConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']

        if self.user_id is None:
            logger.info("User id is not present in url config") 
            self.close()
            return 
        self.group_name = f"user_{self.user_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        
    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        await self.channel_layer.group_send(
            self.group_name, {"type": "send_message", "message": f"Hello from group {self.group_name}"}
        )

    async def send_message(self, event):
        import json
        await self.send(text_data=json.dumps({"message": event['message']}))

    