from rest_framework.permissions import BasePermission, SAFE_METHODS

class CanRateOrReview(BasePermission):
    def has_permission(self, request, view):
        current_user = request.user

        if current_user.is_superuser or current_user.is_staff:
            return True
        
        return current_user.is_customer

class CanModifyReviewOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        
        current_user = request.user
        if current_user.is_superuser or current_user.is_staff:
            return True
        
        return obj.reviewed_by == current_user
    
class CanModifyRatingOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_superuser or request.user.is_staff:
            return True
        return request.user == obj.rate_by
    
