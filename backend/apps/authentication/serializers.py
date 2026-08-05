from phonenumber_field.serializerfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as _validate_password
from django.db import transaction
from django.utils import  timezone
from django.db.models import Q

from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, BlacklistedToken, OutstandingToken

from .helpers import validate_email, _get_user_by_email, _get_code_instance_or_none
from .models import CustomUser
from .services.auth_services import google_auth, facebook_auth, apple_auth
from .utils.helpers import (create_otp_for_user)
from .helpers import send_email_to_user, logger
from .utils.template_helpers import genrate_context_for_otp

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class RegistrationsSerializer(serializers.Serializer):
    """
    Serializer for handling new user registration.

    This serializer validates user input for creating a new account, 
    ensures password complexity, and hashes the password before saving 
    to the database.

    Fields:
        
        email (str): A valid email address for account notifications.
        first_name: First name to fill account credentials
        last_name: Last name to fill account credentials
        phone: A unique phone number for account notifications
        password (str): A write-only field for the account password.
        password_confirm (str): A write-only field to verify the password.

    Methods:
        validate: Ensures that password and password_confirm match.
        create: Handles the actual user creation and password hashing.
    """

    email = serializers.EmailField(max_length=200)
    first_name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200)
    phone = PhoneNumberField(max_length=50)
    password = serializers.CharField(write_only=True, max_length=50)
    
    confirm_password = serializers.CharField(max_length=50, write_only=True)
    referral_code = serializers.CharField(max_length=20, write_only=True, required=False, allow_blank=True)


    def to_representation(self, instance):
        data = super().to_representation(instance)

        logger.debug(f"Data rep. {data}")
        # Ensure Phone number field is serialized to string
        data["phone"] = str(instance.phone) if instance.phone else None

        return data

    def validate_phone(self, value):
        """
        This method ensures that the provided email address does not already 
        exist in the database and complies with company domain restrictions.
        """
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone already exists", code="phone_exists")
        return value
    
    def validate_email(self, value:str):
        """
        Check if the email is unique and belongs to an authorized domain.

        This method ensures that the provided email address does not already 
        exist in the database and complies with company domain restrictions.

        Args:
            value (str): The email address string provided by the user.

        Returns:
            str: The validated email address if all checks pass.

        Raises:
            serializers.ValidationError: If the email is already registered 
                or uses a forbidden domain.
        """ 
        email = value.strip().lower()
        valid_email = validate_email(email)
        user = User.objects.filter(email=valid_email)
        if user.exists():
            if user.is_verified and user.is_active:
                raise serializers.ValidationError(_("email already exists"), code="email_exists")
            else:
                # fallback to resending email when a user account isn't verified yet
                code = create_otp_for_user(user)
                context = genrate_context_for_otp(code=code, email=user.email, full_name=user.full_name)
                send_email_to_user(context)
        return valid_email

    def validate(self, attrs):
        """
        Normalize the `first_name` and `last_name` fields in the given attributes
        dictionary by converting them to title case.

        If a name field is missing, empty, or falsy, it will be set to None.
        The function mutates and returns the same dictionary.

        Args:
            attrs (dict): A dictionary that may contain 'first_name' and 'last_name'.

        Returns:
            dict: The updated attributes dictionary with normalized name fields.
        """
    
        try:
            password = attrs.get("password")
            confirm_password = attrs.get("confirm_password")
            if not password or  not confirm_password:
                            raise serializers.ValidationError({"Password": _("Both password fields are required")})
            
            if password.strip() != confirm_password.strip():
                raise serializers.ValidationError(_("your password do not match"))

        except (Exception, TypeError) as exc:
            logger.exception("Error while checking password")
            raise serializers.ValidationError(_("Error while checking password"))

        for field in ("first_name", "last_name"):
            value = attrs.get(field)
            attrs[field] = value.title() if value else None
        return attrs


    def _normalize_and_validate_password(self, value):
        
        return _validate_password(value.strip())

    def validate_password(self, value):
        """
        Validate and normalize the user's password.

        Strips leading and trailing whitespace from the password and delegates
        password strength and rule enforcement to the internal `_validate_password`
        helper.
        """
        try:
            self._normalize_and_validate_password(value)
        except Exception as exc:
            logger.exception("Password validation error: %s", exc)
            raise serializers.ValidationError("Error validating password")
        return value

    def validate_confirm_password(self, value):
        try:
            self._normalize_and_validate_password(value)
        except Exception as exc:
            logger.exception("Confirm password validation error: %s", exc)
            raise serializers.ValidationError("Error validating confirm password")
        return value


    def create(self, validated_data):
        """
        Create a new user with the validated data.

        This method ensures that the user is created using the `create_user` method,
        which handles hashing passwords securely. It also includes basic logging and
        error handling for edge cases.

        Args:
            validated_data (dict): A dictionary of validated data for creating the user.

        Returns:
            User: The newly created user object.

        Raises:
            ValidationError: If the user creation fails due to invalid data.
        """

        try:
            confirm_password = validated_data.pop("confirm_password")
            referral_code = validated_data.pop("referral_code", None)
            
            with transaction.atomic():
                user = User.objects.create_user(**validated_data)
            logging.info(_(f"A new user instance created: {user.full_name}"))

            if referral_code is not None:
                    from ..referral.tasks import process_referral_attchement

                    code = referral_code
                    logger.info("saving user to referral")
                    process_referral_attchement.delay(referred_user_id=user.pk, code_str=code)
                   
            return user
        except Exception as exc :
            logger.exception("User creation failed: %s", exc)
            raise serializers.ValidationError("User creation failed")

class AccountVerificationSerializer(serializers.Serializer):
    """
    Serializer for verifying a user's account using an email address and a verification code.

    Validates:
        - Email: Must be a valid, deliverable email address.
        - Code: Must be a non-empty string.

    Both fields are write-only and required.
    """
    code = serializers.CharField(max_length=50, write_only=True, required=True)
        
    def validate_code(self, value):
        if not isinstance(value, str):
            raise serializers.ValidationError(_(f"String instance expected, but got {type(value)}"))
        return value.strip()
    
    def validate(self, attrs):
        code = attrs["code"]

        code_instance = _get_code_instance_or_none(code=code)
       
        if code_instance is None:
            raise serializers.ValidationError(_("OneTImePassword Not Found"), code="not_found")

        if code_instance.is_expired():
            raise serializers.ValidationError(_("Code Already expired"), code="expired")
        
        if not code_instance.is_active or code_instance.is_used:
            raise serializers.ValidationError(_('code already expired'), code="invalid_code")
        return attrs

class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=50, write_only=True, required=True)

    def validate_email(self, value):
        valid_email = validate_email(value.lower())
        user = _get_user_by_email(valid_email)
        if not user:
            raise serializers.ValidationError(_('User not found'), code="email_invalid")
        return valid_email

class PasswordResetConfirmSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50, write_only=True, required=True)
    password = serializers.CharField(write_only=True, max_length=200)
    confirm_password = serializers.CharField(write_only=True, required=True, max_length=200)

    def validate_code(self, value):
        code_instance = _get_code_instance_or_none(value.strip())
        if code_instance is None:
            raise serializers.ValidationError(_("OneTimePassword object not found"))
        
        if code_instance.is_expired():
            raise serializers.ValidationError(_("code already expired"), code="expired")
        if not code_instance.is_active or code_instance.is_used:
            raise serializers.ValidationError(_('code already expired'), code="invalid_code")

        return code_instance
    
    def validate_password(self, value):
        _validate_password(value)
        return value
    
    def validate_confirm_password(self, value):
        _validate_password(value)
        return value

    def validate(self, attrs):
        password = attrs.get("password", None)
        confirm_password = attrs.get("confirm_password", None)
        if password is None or confirm_password is None:
            raise serializers.ValidationError(_("Password reset requires 'password' and 'confirm_password'"))
        if password.strip() != confirm_password.strip():
            raise serializers.ValidationError(_("Password Mismatch. Please provide a matching password"))
        return attrs

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def user_can_authenticate(self, user):
        if hasattr(user, "is_active") and hasattr(user, "is_verified"):
            return user.is_active and user.is_verified
        return False
        
    def validate(self, attrs):
        password = attrs.get("password")
        email = attrs["email"]
        valid_email = validate_email(email=email, check_deliverability=True)

        if valid_email is None:
            raise serializers.ValidationError(_("email returned none when verifying email address"))
        try:
            user = User.objects.get(email=valid_email) 
        except User.DoesNotExist:
            raise AuthenticationFailed(code="invalid_credentials", detail={"status": "Failed", "message": f"Invalid credentials"})
        
        if not self.user_can_authenticate(user):
            raise AuthenticationFailed(code="invalid_request", detail={"status": "Failed", "detail": _("invalid credentials")})
        
        if not user.check_password(password):
            raise AuthenticationFailed(code="invalid_credentials", detail={"status": "failed", "detail": _("invalid_credentials")})
        
        self.user = user
        data = super().validate(attrs)
        serializer = UserReadSerializer(user, context=self.context)
        data.update({"user_data": serializer.data})
        self.user.last_login = timezone.now()
        self.user.save()

        return data
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token.verify()
        token.set_jti()
        token["email"] = getattr(user, "email", None)
        token["full_name"] = getattr(user, "full_name", None)

        return token

class CustomLogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True, write_only=True, error_messages={
        "required": _("Refresh token is required to logout.")
    })
    default_error_messages = {
        "bad_token": _("Token is invalid or expired")
    }


class UserReadSerializer(serializers.ModelSerializer):
    from apps.users.serializers.profiles import BaseProfileListSerializer
    profile = BaseProfileListSerializer(read_only=True)
    class Meta:
        model = User
        fields = [
            "user_id", "phone",
            "email", "first_name", "last_name", 
            "is_provider", "is_customer",
            "is_verified", "profile"
        ]   


class CustomRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user):
        data = super().for_user(user)
        data['email'] = user.email
        return data

class SocialAuthSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        provider: str = self.context.get("provider")
        if provider is None:
            raise serializers.ValidationError("Invalid Request: provider is not present")
        
        if provider.upper() not in CustomUser.AuthProviders.values:
            raise serializers.ValidationError("provider is not in valid options")

        data['provider'] = provider.upper()
        return data
    

    def create(self, validated_data):
        provider = validated_data['provider']
        token = validated_data['token']

        user_info = None

        if provider == CustomUser.AuthProviders.GOOGLE:
           user_info = google_auth(token=token)
        elif provider == CustomUser.AuthProviders.FACEBOOK:
            user_info = facebook_auth(token=token)
        elif provider == CustomUser.AuthProviders.APPLE:
            user_info = apple_auth(token=token)
        else:
            raise serializers.ValidationError("invalid Request")

        if not user_info.get("status"):
            raise serializers.ValidationError(user_info)
        if not "email" or "phone" in user_info:
            raise serializers.ValidationError("Phone or email adddress is not present in user info")
        
        # sign up either with email or phone nmber
        try:
            email = user_info.get("email")
            default_kwargs = {
                "email": email, "username": user_info.get("name"),
                "is_active": True, "is_verified": True if user_info.get("email_verified") else False
            }
            user, created = CustomUser.objects.get_or_create(email=email,
                defaults=default_kwargs
            )
            user.last_login = timezone.now()
            refresh = CustomRefreshToken().for_user(user)
            user_data = UserReadSerializer(user, context=self.context).data
            response = {"refresh_token": str(refresh), "access_token": str(refresh.access_token), "user_data": user_data}
            user.save()
            return response
        except Exception as exc:
            logger.exception("Social authentication create failed: %s", exc)
            raise serializers.ValidationError("Social authentication failed")