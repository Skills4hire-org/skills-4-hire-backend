from channels.generic.websocket import AsyncJsonWebsocketConsumer
import logging 
from .services import create_notification
from .events import NotificationEvents
from channels.db import database_sync_to_async
import json
from .helpers import booking_notifications, booking_payment_notification

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
    

    async def booking_notification(self, event):
        event_type =  NotificationEvents.BOOKING.value
        message = event['event_type']
        sender_id = event['sender_id']
        receiver_id = event['receiver_id']
        notification = await self.save_notification(
            event_type=event_type, sender=sender_id, receiver=receiver_id, message=message)
        

        await self.send(text_data=json.dumps({
            "type": message,
            "booking_id": event['booking_id'],
            "sender_id": sender_id,
            "event_type": event_type,
            "receiver_id": receiver_id
        }))

    async def booking_pay(self, event):
        event_type = NotificationEvents.PAYMENT.value
        message = event['event_type']
        sender_id = event['sender_id']
        receiver_id = event['receiver_id']
        notification = await self.save_notification(
            event_type=event_type, sender=sender_id, 
            receiver=receiver_id, message=message)

        await self.send(text_data=json.dumps({
            "type": message,
            "is_debit": event['is_debit'],
            "is_credit": event['is_credit'],
            "amount": event['amount'],
            "sender_id": str(sender_id),
            "receiver_id": str(receiver_id)
        }))

    @database_sync_to_async
    def save_notification(self, event_type, sender, receiver, message):
        return create_notification(
            event=event_type, message=message, sender=sender, receiver=receiver
        )

def broadcast_notification(event_type: str, payload: dict): 
    if not event_type:
        logger.info("cant broadast message with no event")
        return
    
    if event_type in ("booking_made", "booking_approved", "booking_rejected"):
        booking = payload['booking']
        sender = None
        receiver = None
        match event_type:
            case "booking_made":
                sender = booking.customer
                receiver = booking.provider.profile.user
            case "booking_approved":
                sender = booking.accepted_by
                receiver = booking.customer
        
            case "booking_rejected":
                sender = booking.rejected_by
                if sender == booking.customer:
                    receiver = booking.provider.profile.user
                else:
                    receiver = booking.customer
            case _:
                booking = None
        booking_notifications(sender, receiver, booking.pk, event_type)
        
    elif event_type in ('booking_credit', "booking_debit", 'payment_request'):
        booking_payment_notification(payload, event_type)







    

