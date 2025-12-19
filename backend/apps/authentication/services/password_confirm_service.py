from apps.authentication.services.baase_service import BaseService
from django.core.exceptions import ValidationError
from apps.authentication.otp_models import OTP_Base
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.cache import cache
import logging 

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
            code_instance  = get_object_or_404(OTP_Base, code=code)
            
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

            check_token = token_generator.check_token(user, token)
            if not check_token:
                raise ValidationError("Password reset token mismatch. Error")
            
            cache_key = f"token_{user.pk}_cache"

            logger.debug(f"DEBUG CACHED KEYS {cache.keys()}")
            if not cache.get(cache_key, None):
                raise ValidationError("Cached token already expired: Timedout")
            return True 
        except Exception as exc:
            raise ValidationError(f"Error: {exc}")


    def clean_up_jobs(self, code, user):

        if not (user, code):
            raise ValidationError("Both 'user', and 'code' are required to clean up jobs")

        # Delete otp and redis cache
        cache_key = f"token_{user.pk}_cache"
        OTP_Base.objects.get(code=code).delete()
        cache.delete(cache_key)


        

#{
 #   "code": "0393940S",
  #  "password": "09876poiu",
   # "confirm_password": "09876poiu"
#}