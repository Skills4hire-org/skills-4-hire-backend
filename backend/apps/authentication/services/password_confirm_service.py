from .base import BaseService
from django.core.exceptions import ValidationError
from apps.authentication.one_time_password import OneTimePassword
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import logging 
from ..utils.helpers import _hash_otp_code
from django.core.cache import cache
from apps.authentication.helpers import blacklist_outstanding_token
logger = logging.getLogger(__name__)

class PasswordConfirmService(BaseService):


    def _decode_serializer(self):
        if not self._validate_serializer():

            raise ValidationError()

        validated_data = self.serializer.validated_data
        password = validated_data.get("password")
        code = validated_data.get("code")

        if not (password and code):
            raise ValidationError("Both 'password' and 'confirm' password' is required")

        return code, password


    def validate_code(self, code):
        """ A method that take otp code and check is still valid

            return:
                User object
        """

        if not code:
            raise ValidationError("code is required for password reset")

        try:
            hashed_code = _hash_otp_code(code)
            code_instance  = get_object_or_404(OneTimePassword, code=hashed_code)
            
            if code_instance.is_expired() or code_instance.is_used:
                raise ValidationError("code is compromised. \n Invalid code provided")

            return code_instance.user

        except Exception as exc:
            raise ValidationError(f"Error {exc}")



    def pasword_reset_token_check(self, user, token):
        if not (user and  token):
            raise  ValidationError("Both fields is requireed 'user', 'token'")

        try:
            token_generator = PasswordResetTokenGenerator()

            if not token_generator.check_token(user, token):
                raise ValidationError("Token generation check mismatch")

            cache_key = f"password_reset:{user.pk}".strip()

            redis_cache_key = cache.get(cache_key)
            if not redis_cache_key:
                raise ValidationError("Cached token Not found: Timedout")

            if not token_generator.check_token(user, redis_cache_key):
                raise ValidationError("Token Mismatch with redis", code=400)

            cache.delete(cache_key)
            return True
        
        except Exception as exc:
            raise ValidationError(f"Error: {exc}")


    def clean_up_jobs(self, code, user):

        if not (user, code):
            raise ValidationError("Both 'user', and 'code' are required to clean up jobs")

        hashed_code = _hash_otp_code(code)
        OneTimePassword.objects.get(user=user, code=hashed_code).delete()

        # Clean up all outstanding tokens after password change
        blacklist_outstanding_token(user)



        

