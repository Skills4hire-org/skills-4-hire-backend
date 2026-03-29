from rest_framework.permissions import BasePermission


class IsEndorsementCreateUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_customer

    
    def has_object_permission(self, request, view, obj):

        if request.user.is_superuser or request.user.is_staff:
            return True
        return obj.endorsed_by == request.user


class IsSubject(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        return obj.provider == request.user.profile.provider_profile