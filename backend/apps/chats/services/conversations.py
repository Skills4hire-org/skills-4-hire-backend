from ..models import Conversation

from django.db import transaction, IntegrityError

from rest_framework.exceptions import NotFound


class ConversationService:
    def __init__(self, sender, receiver):
        self.sender = sender
        self.receiver = receiver


    def _validate_required_attribute(self):
        if self.sender is None:
            raise NotFound("User not found", code=404)
        if self.receiver is None:
            raise NotFound("receiver not found", code=404)

        return  True

    @transaction.atomic
    def create_conversation(self, **kwargs):
        if not self._validate_required_attribute():
            return False
        try:
            new_conversation = Conversation.objects.create(
                sender=self.sender,
                receiver=self.receiver,
                **kwargs
            )
        except IntegrityError as e:
            raise IntegrityError(e)
        except Exception as e:
            raise Exception(e)

        return  new_conversation
