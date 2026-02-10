from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user")
        if not user.is_authenticated:
            return False
        user_profle = getattr(user, "profile")
        if obj.profile == user_profle:
            return True
        return False