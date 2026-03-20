import random
import pytest

from ....factories import (
    ConversationFactory, NegotiationFactory,
)

@pytest.fixture
def conversation_fixture(customer, provider):
    return ConversationFactory(
        participant_one=customer,
        participant_two=provider
    )

@pytest.fixture
def can_negotiate_fixture(conversation_fixture, customer, provider):
    senders = (customer, provider)
    return NegotiationFactory(
        conversation=conversation_fixture,
        sender=random.choice(senders),
        price=random.randint(100, 1000)
    )

@pytest.fixture
def cannot_negotiate_fixture(conversation_fixture, customer, provider):
    completed_negotiation = ("ACCEPTED", "REJECTED")
    senders = (customer, provider)
    return  NegotiationFactory(
        conversation=conversation_fixture,
        sender=random.choice(senders),
        status=random.choice(completed_negotiation),
        price=random.randint(100, 1000)
    )