from phonenumber_field.serializerfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as _validate_password
from django.db import transaction
from django.utils import  timezone

from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, BlacklistedToken, OutstandingToken

from .helpers import validate_email, _get_user_by_email, _get_code_instance_or_none
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
            raise serializers.ValidationError("Phone number already exists")
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
        if User.objects.filter(email=valid_email).exists():
            raise serializers.ValidationError(_("A user with this email already exist"))
        
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
            if password and confirm_password:
                if password.strip() != confirm_password.strip():
                    raise serializers.ValidationError(_("your password do not match"))
            elif not password or  not confirm_password:
                raise serializers.ValidationError({"Password": _("Both password fields are required")})
        except (Exception, TypeError) as exc:
            raise serializers.ValidationError(_(f"Error while checking password: {exc}"))

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
            raise serializers.ValidationError(f"error occurred:{exc}")
        return value

    def validate_confirm_password(self, value):
        try:
            self._normalize_and_validate_password(value)
        except Exception as exc:
            raise serializers.ValidationError(f"error occurred: {exc}")
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
            with transaction.atomic():
                user = User.objects.create_user(**validated_data)

            logging.info(_(f"A new user instance created: {user}"))

            return user
        except Exception:
            logging.error(_(f"user creation failed:"))
            raise serializers.ValidationError("User creation Failed!")

    
class AccountVerificationSerializer(serializers.Serializer):
    """
    Serializer for verifying a user's account using an email address and a verification code.

    Validates:
        - Email: Must be a valid, deliverable email address.
        - Code: Must be a non-empty string.

    Both fields are write-only and required.
    """
    email = serializers.EmailField(max_length=200, write_only=True, required=True)
    code = serializers.CharField(max_length=50, write_only=True, required=True)

    def validate_email(self, value: str):
        return validate_email(value)
        
    def validate_code(self, value):
        if not isinstance(value, str):
            raise serializers.ValidationError(_(f"String instance expected, but got {type(value)}"))
        return value.strip()
    
    def validate(self, attrs):
        email, code = attrs["email"], attrs["code"]

        user = _get_user_by_email(email=email)
        if user is None:
            raise serializers.ValidationError(_("User not found"), code="user_not_found")
        code_instance = _get_code_instance_or_none(code, user=user)
       
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
        
        user = code_instance.user
        if not user.is_active or user.is_verified:
            raise serializers.ValidationError("Account not verified")
        return value
    
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
        valid_email = validate_email(email)

        if valid_email is None:
            raise serializers.ValidationError(_("email returned none when verifying email address"))
        try:
            user = User.objects.get(email=valid_email) 
        except User.DoesNotExist:
            raise AuthenticationFailed(code="invalid_credentials", detail={"status": "Failed", "message": f"account not found for user {valid_email}"})
        
        if not self.user_can_authenticate(user):
            raise AuthenticationFailed(code="invalid_request", detail={"status": "Failed", "detail": _("account not verified")})
        
        if not user.check_password(password):
            raise AuthenticationFailed(code="invalid_credentials", detail={"status": "failed", "detail": _("invalid_credentials")})
        
        self.user = user
        data = super().validate(attrs)
        data.update({"user_data": {
            "user_id": user.pk, "email": user.email,
            "name": getattr(user, "full_name") or "",
            'is_customer': user.is_customer,
            'is_provider': user.is_provider
        }})
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

    def get_user_from_token(token: str):
        token = RefreshToken(token=token)
        return token.get("user_id")
    
    def validate(self, attrs):
        data = super().validate(attrs)
        request = self.context.get("request")
        user = request.user 
        if user is None or "Anonymous": 
            raise serializers.ValidationError(_("Authentication credentials were not provided"), code="invali_request")
        token = attrs.get("refresh_token")
        user_id = self.get_user_from_token(token)
        if user_id != user.pk:
            raise serializers.ValidationError(_("Invalid Request. refresh token is Invalid"), code="refresh_token_invalid")
        with transaction.atomic():
            outstanding_tokens = OutstandingToken.objects.filter(user=user).all()
            # black list all outstanding token for this user
            BlacklistedToken.objects.bulk_create(
                BlacklistedToken(token=token) for token in outstanding_tokens
            )
        return attrs

class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email", "first_name",
            "last_name",
            "is_provider", "is_customer",
            "phone",
            "is_active", "is_verified",
            
        ]   
