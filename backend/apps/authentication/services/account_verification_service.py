
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import logging
from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from apps.authentication.otp_models import OTP_Base
from apps.authentication.exceptions import ServiceAlreadyExpired
from apps.authentication.services.baase_service import BaseService


User = get_user_model()
logger = logging.getLogger(__name__)


class AccountVerificationService(BaseService):
    
    def _decode_serializer(self):
        if not self._validate_serializer():
            logger.error("Serializer validation failed in decode_serializer.")
            raise ValidationError("Invalid serializer data.")

        validated_data = self.serializer.validated_data
        email = validated_data.get("email", None)
        code = validated_data.get("code", None)

        if not email or not code:
            logger.warning("")
            raise ValidationError("Both 'email' or 'code' must be provided")

        return email, code

    def get_user(self, user_email: str) -> User:
        if not user_email:
            logging.error("Email is required to get user instance")
            raise ValidationError("Email is required")
        try:
            user = get_object_or_404(User, email=user_email)

            # check if account is still active 
            if user.is_deleted:
                raise ValidationError("Account has been deactivated. contact support")

            if user.is_verified or user.is_active:
                return "Your account is verified, login to your account"

            return user
        except DatabaseError as exc:    
            logger.error(" Hit Database error while Retrieving user instance %s", user_email, exc_info=True)
            raise ValidationError("Database error while retrieving user instance for account verification.") from exc
        except ValueError as exc:
            logger.error("Invalid request for  %s", user.id, exc_info=True)
            raise ValidationError(f"error while retrieving user instance for {user_email}")


    def get_otp_instance(self, user, code):
        if not user or not code:
            raise ValidationError("Request is misconfigured. Both fields are requried 'user instance', and  'code'.")

        try:
            otp_instance = get_object_or_404(OTP_Base, user=user, code=code)

            if otp_instance.is_expired:
                logging.info("OTP instance is Expired")
                raise ServiceAlreadyExpired("otp instance is expired ")

            return otp_instance
        except DatabaseError:
            pass
    
    def _verify_account(self, otp_instance, user_instance):
        try:

            if otp_instance.user == user_instance:
                user_instance.is_active = True
                user_instance.is_verified = True

                otp_instance.is_used = True

                user_instance.save(update_fields=["is_active", "is_verified"])

                otp_instance.save(update_fields=['is_used'])
                S
        except DatabaseError as exc:
            logger.error("error while verifying user account", exc_info=True)
            raise ValidationError("Error while validating user and otp instances", exc)

        except Exception as e:
            raise ValidationError("Inappropriate error occured", e)

            