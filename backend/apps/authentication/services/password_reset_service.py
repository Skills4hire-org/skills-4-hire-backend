from apps.authentication.services.baase_service import BaseService
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.conf import settings
from apps.authentication.services.resend_otp_service import ResendOtpService
from apps.authentication.helpers import send_email_to_user
from apps.authentication.services.email_services import EmailService


import logging
logger = logging.getLogger(__name__)
cache_ttl = getattr(settings, "OTP_EXPIRY", 15)

class PasswordResetService(ResendOtpService):

    def generate_token_for_user(self, user):
        if user is None:
            logger.error("User intance is not provided to generate token")
            raise ValidationError("User instance is required when generating token for user")
        
        try:
            generate_token = PasswordResetTokenGenerator()

            token = generate_token.make_token(user=user)

            return token
        except Exception as exc:
            logger.exception("Exception occurred while generating token for user %", user.pk)
            raise ValidationError("Validating and returning password reset token failed")
        
    def create_cache_key(self, user_pk):
        token_cache_key = f"token_{user_pk}_cache"

        return token_cache_key

    def cache_token_in_redis_cache(self, user, token):  
        if not  (user and token):
            return None
        
        cache_key = self.create_cache_key(user.pk)

        if not cache.has_key(cache_key):
            cache.set(cache_key, token, timeout=cache_ttl)

        return cache_key

    def send_reset_email(self, code, user):
        try:
            name = user.full_name
            template = "authentication/password_reset.html"

            subject, context = EmailService.pasword_reset_message(name=name, code=code)

            send_email_to_user(subject, context, template, user.email)
        except Exception as exc:
            raise ValidationError(f"Failed to send email {exc}")
    

        



