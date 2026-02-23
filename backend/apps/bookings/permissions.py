from rest_framework.permissions import BasePermission

from django.contrib.auth import get_user_model

from .helpers import user_in_booking

User = get_user_model()

class IsCustomer(BasePermission):
    """ Allow access to customers"""
    def has_permission(self, request, view):
        user_active_role = getattr(request.user, "active_role", None)
        if user_active_role is None:
            return False
        if user_active_role != User.RoleChoices.CUSTOMER:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        active_role = getattr(user, "active_role", None)
        if active_role == User.RoleChoices.CUSTOMER:
            return obj.customer == user
        return False

class IsCustomerOrProvider(BasePermission):
    """ A Custom permission class that grant access to user who's active role is either customer or provider"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.is_staff:
            return True
        else:
            if user_in_booking(user, obj):
                return True
        return False
        