from rest_framework.permissions import IsAuthenticatedOrReadOnly
from typing import Any

class IsOwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    """Permission that grants write access to owners only (read for others).

    Extends `IsAuthenticatedOrReadOnly` so unauthenticated requests still
    have read-only access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj: Any) -> bool:

        if request.user.is_authenticated and request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Write permissions only to owner
        return getattr(obj, 'user', None) == getattr(request, 'user', None)