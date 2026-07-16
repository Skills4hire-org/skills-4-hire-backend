

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