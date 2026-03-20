from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.authentication.models import CustomUser

class IsProvider(BasePermission):
    """
    A Custom permissions class for checking is  user is a provider. \n
    Return 'True' if passed 'False' otherwise

    """
    def has_permission(self, request, *args, **kwargs):
        user = request.user
        if not user and not user.is_authenticated:
            return False
        return user.is_provider


class IsSkillOwner(BasePermission):
    """
    A Custom permission class to check if the user is the owner of the skill \n
    Return 'True' if passed 'False' otherwise
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not hasattr(request.user.profile, "provider_profile"):
            return False
        return request.user.profile.provider_profile == obj.profile

class IsProfileOwnerOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.profile.user == request.user

    
        
