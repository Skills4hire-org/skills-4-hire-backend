import channels.layers
from asgiref.sync import async_to_sync
from dotenv import load_dotenv

import django
import os
load_dotenv()

setting_module = os.getenv("DJANGO_SETTINGS_MODULE")

os.environ.setdefault('DJANGO_SETTINGS_MODULE',  setting_module)
django.setup()

def run():
    # from apps.chats.consumers import broadcast_chat_message
    # from apps.chats.models import Message

    # message = Message.objects.first()

    # channel_layer = channels.layers.get_channel_layer()
    # broadcast_chat_message(message=message)
    
    # return async_to_sync(channel_layer.receive)(f'chat_group_{message.conversation.conversation_id}_')


if __name__ == "__main__":
    print(run())
