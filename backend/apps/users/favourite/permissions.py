from rest_framework.permissions import BasePermission, SAFE_METHODS


class CanAddFavourite(BasePermission):
    def has_permission(self, request, view):

        user = request.user
        if not user.is_authenticated:
            return False
        
        if request.method in SAFE_METHODS:
            return True
    
        if user.is_superuser or user.is_staff:
            return True
        return user.is_customer
    

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.is_staff:
            return True
        return obj.owner == user