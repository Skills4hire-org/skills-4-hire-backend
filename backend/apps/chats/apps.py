from django.apps import AppConfig


class ChatsConfig(AppConfig):
    name = 'apps.chats'
    label = "chats"

    def ready(self):
        from .endorsements import signals
        
