from django.core.exceptions import ValidationError
from .account_verification_service import AccountVerificationService
import logging


logger = logging.getLogger(__name__)


class ResendOtpService(AccountVerificationService ):

    def _decode_serializer(self):
        if not self._validate_serializer():
            logger.error("Serialization validations faile")
            raise ValidationError("serializer Validation check failed")

        validated_data = self.serializer.validated_data

        email = validated_data.get("email", None)

        if email is None :
            raise ValidationError("email field is required from the serialized data")

        return email

        def resend_otp(self, user, code):
            if not user or not code:
                raise ValidationError("Both 'user' and 'code' is required to proceed with this operations")

        

    