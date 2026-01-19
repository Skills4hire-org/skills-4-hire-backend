from rest_framework.permissions import BasePermission

from django.contrib.auth import get_user_model

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

class IsCustomerOrProvider(BasePermission):
    """ A Custom permission class that grant access to user who's active role is either customer or provider"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        active_role = getattr(user, "active_role", None)
        if active_role == User.RoleChoices.CUSTOMER:
            return obj.customer == user
        if active_role == User.RoleChoices.SERVICE_PROVIDER:
            if hasattr(user.profile, "provider_profile"):
                provider_profile = getattr(user.profile, "provider_profile")
                return obj.provider == provider_profile
            else:
                raise AttributeError("Service provider has no provider profile")
        return False