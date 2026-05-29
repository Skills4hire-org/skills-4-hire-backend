from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    message = "You do not have permission to modify this service."

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True

        # obj is a Service instance; ownership is via service.profile.profile.user
        return obj.profile.profile.user == request.user

class IsServiceProvider(BasePermission):
    message = "Only service providers can perform this action."

    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and request.user.is_provider