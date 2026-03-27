from rest_framework.permissions import BasePermission

from django.contrib.auth import get_user_model

User = get_user_model()

class IsCustomer(BasePermission):
    """ Allow access to customers"""
    def has_permission(self, request, view):
        return request.user.is_customer or request.user.is_superuser or request.user.is_staff

    def has_object_permission(self, request, view, obj):
       return request.user.is_customer or obj.is_participants(request.user)


class IsProvider(BasePermission):
    """ Allow access to customers"""

    def has_permission(self, request, view):
        return request.user.is_provider or request.user.is_superuser or request.user.is_staff

    def has_object_permission(self, request, view, obj):
        return request.user.is_provider or obj.is_participants(request.user)


class IsBookingParticipants(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True
        return obj.is_participants(request.user)

class IsRequestReceiverOrSender(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    def has_object_permission(self, request, view, obj):
        return obj.booking.is_participants(request.user)
