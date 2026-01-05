from rest_framework.permissions import BasePermission
from apps.authentication.models import CustomUser

class IsProvider(BasePermission):
    """
    A Custom permissions class for checking is  user is a provider. \n
    Return 'True' if passed 'False' otherwise

    """

    def has_permission(self, request, *args, **kwargs):
        return request.user.role == CustomUser.RoleChoices.SERVICE_PROVIDER

    
