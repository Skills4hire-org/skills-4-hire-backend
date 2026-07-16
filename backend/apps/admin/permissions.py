from rest_framework.permissions import BasePermission

ADMIN_ROLES = ['admin', 'super_admin']

class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        # Must have a admin permission before access the view
        user = request.user 
        if not user.is_authenticated:
            return False
        if user.active_role is None:
            return False
        return user.active_role.lower() in ADMIN_ROLES