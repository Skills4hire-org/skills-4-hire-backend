from rest_framework.permissions import BasePermission


class IsNotificationOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.is_staff:
            return True
        elif obj.user == user:
            return True
        return False
    
    
        