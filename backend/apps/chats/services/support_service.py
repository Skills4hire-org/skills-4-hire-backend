from django.db import transaction
from django.db.models import Max, Count, Q
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import Conversation

UserModel = get_user_model()


def get_or_create_support_room(customer):
    """
    Retrieve or create the customer's support room.
    A support room is a special Conversation with room_type SUPPORT.
    The room is created with the customer and a staff user as the two
    conversation participants. All staff users are permitted to access
    support rooms through permission logic rather than direct participant
    assignment.
    """
    if customer is None:
        raise ValueError("Customer is required to open a support room.")
    from datetime import timedelta

    now = timezone.now()
    last_seen = now - timedelta(days=1)
    staff_user = UserModel.objects.filter(is_staff=True, is_active=True, last_login__gt=last_seen).order_by('created_at').first()
    if staff_user is None:
        staff_user = UserModel.objects.filter(is_staff=True, is_active=True).order_by('created_at').first()

    with transaction.atomic():
        support_room, created = Conversation.objects.get_or_create(
            participant_one=staff_user,
            room_type=Conversation.RoomType.SUPPORT,
            defaults={
                "participant_two":customer,
            }
        )

    return support_room


def get_all_support_rooms():
    """
    Return all support rooms ordered by most recent activity.

    Annotates each room with:
    - last_message_at: most recent message timestamp
    - unread_count: number of unread messages sent by non-staff users
    """
    return Conversation.objects.filter(
        room_type=Conversation.RoomType.SUPPORT
    ).select_related(
        'participant_one',
        'participant_two'
    ).prefetch_related(
        'messages'
    ).annotate(
        last_message_at=Max('messages__created_at'),
        unread_count=Count(
            'messages',
            filter=Q(
                messages__is_read=False,
                messages__sender__is_staff=False
            )
        )
    ).order_by('-last_message_at')


def mark_messages_as_read(room, user):
    """
    Mark all unread messages in the room for the current user.

    This uses a bulk update and returns the number of rows changed.
    """
    if room is None or user is None:
        return 0

    messages_to_mark = room.messages.filter(
        is_read=False
    ).exclude(
        sender=user
    )

    updated_count = messages_to_mark.update(is_read=True)
    return updated_count


def add_staff_to_all_support_rooms(staff_user):
    """
    When a new staff user is created, ensure to create access rooms.

    Support rooms are accessible by any staff member through permission logic.
    """
    if staff_user is None or not getattr(staff_user, 'is_staff', False):
        return 0

    support_rooms = Conversation.objects.create(participant_one=staff_user, room_type=Conversation.RoomType.SUPPORT)
    return support_rooms
