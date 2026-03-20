from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import View


class IsOwnerOrReadOnly(BasePermission):

    message = "You do not have permission to modify this service."

    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True

        # obj is a Service instance; ownership is via service.profile.profile.user
        return obj.profile.profile.user == request.user