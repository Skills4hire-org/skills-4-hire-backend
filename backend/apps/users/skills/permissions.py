from rest_framework.permissions import BasePermission, SAFE_METHODS


class SkillsOwnerPermissions(BasePermission):
    def has_permission(self, request, view):
        
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_provider
    

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        
        user = request.user
        if user.is_superuser or user.is_staff:
            return True
        
        return user == obj.provider_profile.profile.user