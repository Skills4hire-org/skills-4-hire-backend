
from ..models import Conversation, Negotiations, Post, NegotiationHistory

from django.db import transaction, IntegrityError
from django.db.models import Q
from django.contrib.auth import  get_user_model

from rest_framework.exceptions import (
    NotFound, APIException, ValidationError,
    PermissionDenied
)
from rest_framework import status

import logging

UserModel = get_user_model()
logger = logging.getLogger(__name__)

class ConversationFound(APIException):
    default_detail = "Conversation between user found"
    default_code = "found"
    status_code = status.HTTP_302_FOUND


class ConversationService:
    def __init__(self, participant_one, participant_two):
        self.participant_one = participant_one
        self.participant_two = participant_two


    def _validate_required_attribute(self):
        if self.participant_two is None:
            raise NotFound("User not found", code=404)
        if self.participant_one is None:
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



class NegotiationService:
    def __init__(self, conversation: Conversation | None = None, post: Post | None = None, sender: UserModel=get_user_model()):
        self.conversation = conversation
        self.post = post
        self.sender = sender


    def validate_sender(self):
        if not self.sender:
            raise ValidationError("User instance is required")
        if self.sender and not isinstance(self.sender, UserModel):
            raise ValidationError("Not a valid UserModel instance")
        return True

    @transaction.atomic
    def create_negotiation(self, **kwargs):
        try:
            self.validate_sender()
            negotiation = Negotiations.objects.create(
                conversation=self.conversation,
                job_post=self.post,
                sender=self.sender,
                **kwargs
            )
            if "status" in kwargs:
                status = kwargs.get("status")
            else:
                status = negotiation.status

            logger.info(
                f"Negotiation {status} On {self.conversation.pk if self.conversation else self.post.pk}"
            )
        except Exception as e:
            raise Exception(e)

        return  negotiation

    @staticmethod
    def accept_negotiation(negotiation: Negotiations, user: UserModel):
        if negotiation.is_accepted():
            raise ValidationError("Already accepted and closed")
        if not negotiation.is_participants(user):
            raise PermissionDenied()
        negotiation.accept()
        if negotiation.is_accepted():
            return  True
        return False

    @staticmethod
    def reject_negotiation(negotiation: Negotiations, user: UserModel):
        if not negotiation.is_participants(user):
            raise PermissionDenied()
        negotiation.reject()
        if negotiation.rejected_at is not None:
            return True
        return False

    @staticmethod
    def counter_negotiation(negotiation: Negotiations, user: UserModel):
        if not negotiation.is_participants(user):
            raise PermissionDenied()
        negotiation.counter()
        if negotiation.countered_at is not None:
            return True
        return False

class NegotiationHistoryService:

    def __init__(self, negotiation: Negotiations, sender: UserModel, price: float, action: str):
        self.negotiation = negotiation
        self.sender = sender
        self.action = action
        self.price = price

    def validate_request(self):
        if self.price is None or self.action is None:
            raise ValidationError("'price' and 'action' can't be empty")

        if self.negotiation is None or self.sender is None:
            raise ValidationError("Can't create a negotiation history without a sender or the negotiation obj")

    @transaction.atomic
    def create_history(self, **kwargs):
        try:

            self.validate_request()

            history = NegotiationHistory.objects.create(
                sender=self.sender,
                negotiation=self.negotiation,
                price=self.price,
                action=self.action,
                **kwargs
            )

            logger.info(f"History Saved for negotiation {self.negotiation.pk} with action {self.action}")
        except Exception as e:
            raise Exception(e)
        return history

