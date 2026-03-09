from ..models import Conversation

from django.db import transaction, IntegrityError
from django.db.models import Q

from rest_framework.exceptions import NotFound, APIException
from rest_framework import status

import logging

logger = logging.getLogger(__name__)

class ConversationFound(APIException):
    default_detail = "Conversation for user found"
    default_code = "found"
    status_code = status.HTTP_302_FOUND


class ConversationService:
    def __init__(self, participant_one, participant_two):
        self.participant_one = participant_one
        self.participant_two = participant_two


    def _validate_required_attribute(self):
        if self.sender is None:
            raise NotFound("User not found", code=404)
        if self.receiver is None:
            raise NotFound("receiver not found", code=404)

        return  True

    def _validate_users(self):
        conversation = Conversation.active_objects.filter(
            Q(participant_one=self.participant_one, participant_two=self.participant_two) |
            Q(participant_two=self.participant_one, participant_one=self.participant_two)
        )
        if conversation.exists():
           return  True
        return  False

    @transaction.atomic
    def create_conversation(self, **kwargs):
        if not self._validate_required_attribute():
            return False

        if self._validate_users():
            raise ConversationFound()

        try:
            new_conversation = Conversation.objects.create(
                participant_one=self.participant_one,
                participant_two=self.participant_two,
                **kwargs
            )
            logger.info(f"Conversation created and save between {self.participant_two.pk} <> {self.participant_one.pk}")
        except IntegrityError as e:
            raise IntegrityError(e)
        except Exception as e:
            raise Exception(e)

        return  new_conversation
