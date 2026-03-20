from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAddressOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user_profile.user == request.user

