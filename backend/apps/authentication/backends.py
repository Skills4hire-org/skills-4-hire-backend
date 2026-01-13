from django.contrib.auth.backends import ModelBackend

from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotFound
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

UserModel = get_user_model()
class EmailPhoneBackend(ModelBackend):
    """ 
    Custom backend for authenticating user using email and phone
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        if username is None and password is None:
            return
        try:
            user = UserModel.objects.filter(
                Q(email__iexact=username) |
                Q(phone__iexact=username)
            ).first()
        except UserModel.DoesNotExist:
            UserModel().set_password(password)

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        raise PermissionDenied("Invalid credentials")

    
    def get_user(self, user_id):
        try:
            user = get_object_or_404(UserModel, pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
        

        