"""
Core permission classes used across the application.

These permission classes provide role-based and object-level access control.
"""

from rest_framework.permissions import BasePermission, IsAuthenticated


class IsOwner(BasePermission):
    """
    Permission class to check if the requesting user is the owner of an object.

    Assumes the object has an 'owner' or 'user' field.
    """

    message = 'You are not the owner of this object'

    def has_object_permission(self, request, view, obj):
        # Check if object has 'owner' attribute
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        # Check if object has 'user' attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # Check if it's a user object itself
        return obj == request.user


class IsParticipant(BasePermission):
    """
    Permission class to check if the requesting user is a participant of a conversation.

    Used at both list and object levels.
    """

    message = 'You are not a participant of this conversation'

    def has_permission(self, request, view):
        # Allow authenticated users to attempt access
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user is a participant of the conversation.

        obj is expected to be a Conversation instance.
        """
        if not hasattr(obj, 'participant_one'):
            return False
        participants = (obj.participant_two, obj.participant_one)
        return request.user in participants


class IsMessageSenderOrReadOnly(BasePermission):
    """
    Permission class for messages allowing sender to modify, others can only read.

    Used for message updates/deletes.
    """

    message = 'You can only modify messages you sent'

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed to participants
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return (obj.conversation.participant_one == request.user or
                    obj.conversation.participant_two == request.user)

        # Write permissions only for message sender
        return obj.sender == request.user


class IsAuthenticatedAndNotBlocked(IsAuthenticated):
    """
    Permission class that checks if user is authenticated and not blocked.

    Can be extended to check user blocking/muting status.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)

        if not is_authenticated:
            return False

        # Add custom logic here for blocked users
        # Example: return not request.user.is_blocked

        return True


class ConversationParticipantPermission(BasePermission):
    """
    Combined permission class for conversation-related operations.

    - User must be authenticated
    - User must be a participant of the conversation
    """

    message = 'You do not have permission to access this conversation'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # For conversation objects
        if hasattr(obj, 'participant_one'):
            return (obj.participant_one == request.user or
                    obj.participant_two == request.user)

        # For message objects - check conversation participation
        if hasattr(obj, 'conversation'):
            conversation = obj.conversation
            return (conversation.participant_one == request.user or
                    conversation.participant_two == request.user)

        return False