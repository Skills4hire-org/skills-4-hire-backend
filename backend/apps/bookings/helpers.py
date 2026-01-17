from rest_framework.serializers import ValidationError

from ..authentication.models import CustomUser

def check_request(request):
    if not hasattr(request, "user"):
        raise AttributeError("request is not a valid HTTP request instance")
    return True
    
def check_user_wallet(request):
    if check_request(request):
        if hasattr(request.user, "wallet"):
            return request.user.wallet
    return False

def is_customer(request):
    if check_request(request):
        role = getattr(request.user, "active_role", None)   
        if role is None:
            raise ValidationError("Role is not set for user, Complete onboarding to continue")
        if role == CustomUser.RoleChoices.CUSTOMER:
            return True
    return False