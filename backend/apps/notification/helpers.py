
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync 

channel_layer = get_channel_layer()

def booking_notifications(sender, receiver, booking_id, event_type):
    group_name = f"user_{str(receiver.user_id)}"
    async_to_sync(channel_layer.group_send)(
        group_name, {
            "type": "booking_notification",
            "sender_id": str(sender.user_id),
            "receiver_id": str(receiver.user_id),
            "event_type": event_type,
            "booking_id": str(booking_id)
        }
    )
 


def booking_payment_notification(payload: dict, event_type):
    group_name = f"user_{str(payload['receiver'].user_id)}"
    sender = payload['sender']
    receiver = payload['receiver']
    async_to_sync(channel_layer.group_send)(
        group_name, {
            "type": "booking_pay",
            "sender_id": str(sender.user_id),
            "receiver_id": str(receiver.user_id),
            "is_credit": payload['is_credit'],
            "is_debit": payload['is_debit'],
            "amount": str(payload['amount']),
            "event_type": event_type
        }
    )
