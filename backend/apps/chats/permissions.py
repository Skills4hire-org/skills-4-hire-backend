from rest_framework.permissions import  BasePermission

class ConversationOwner(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return  True

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser or user.is_staff:
            return  True

        if obj.sender == user or obj.receiver == user:
            return  True
        return  False