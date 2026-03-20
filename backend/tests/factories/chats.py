from .users import CustomUserFactory
from apps.chats.models import Conversation, Negotiations

import factory

class ConversationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Conversation

    participant_one = factory.SubFactory(CustomUserFactory)
    participant_two = factory.SubFactory(CustomUserFactory)

class NegotiationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Negotiations

    conversation = factory.SubFactory(ConversationFactory)
    sender = factory.SubFactory(CustomUserFactory)
