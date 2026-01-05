from rest_framework import serializers,status
from phonenumber_field.serializerfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
import email_validator
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as _validate_password
from .models import CustomUser
import logging
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken, BlacklistedToken
logging.basicConfig(level=logging.INFO)


User = get_user_model()

def validate_email(email):
    try:
        valid_email = email_validator.validate_email(email, check_deliverability=True)
    except email_validator.EmailNotValidError as exc:
        raise serializers.ValidationError("Invalid email address provided")
    return valid_email.normalized


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

        logging.debug(f"Data rep. {data}")
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
            user = User.objects.create_user(**validated_data)

            logging.info(_(f"A new user instance created: {user}"))

            return user
        except Exception as exc:
            logging.error(_(f"user creation failed: {exc}"))

            raise ValidationError(detail={
                "success": False,
                "message": _(f"Error: {exc}")
            }, code=status.HTTP_400_BAD_REQUEST)

    
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


    def validate_email(self, value):
        
        email = value.lower()
        return validate_email(email)
        
    
    def validate_code(self, value):
        if not isinstance(value, str):
            raise serializers.ValidationError("A string instance is only allowed")

        return value.strip()

class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=50, write_only=True, required=True)

    def validate_email(self, value):
        email = value.lower()

        return validate_email(email)


class PasswordResetConfirmSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50, write_only=True, required=True)
    password = serializers.CharField(write_only=True, max_length=200)
    confirm_password = serializers.CharField(write_only=True, required=True, max_length=200)

    def validate_code(self, value):
        return value.strip()

    def validate(self, attrs):
        
        password = attrs.get("password", None)
        confirm_password = attrs.get("confirm_password", None)

        _validate_password(password)
        _validate_password(confirm_password)

        if password.strip() != confirm_password.strip():
            raise serializers.ValidationError(_("your password do not match"))

        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def user_can_authenticate(self, user):

        return getattr(user, "is_active", True)
    
    def validate(self, attrs):
        
        login_identifier = attrs.get("email", None)
        password = attrs.get("password", None).strip()
        
        try: 
            user = User.objects.filter(
                Q(email__iexact=login_identifier) |
                Q(phone__iexact=login_identifier)
            ).first()

        except User.DoesNotExist:
            user = None

        if not user.is_verified or  not user.is_active:
            raise serializers.ValidationError("Your account is not verified")
        if user.is_deleted:
            raise serializers.ValidationError("Account has been deactivated, contact admin")
        
        if hasattr(user, "check_password"):
            if not user or not user.check_password(password) or not  self.user_can_authenticate(user):
                raise serializers.ValidationError("Invalid credentials provided")

        self.user = user
        data = super().validate(attrs)

        data["user_data"] = {
            "user_id": user.pk,
            "email": user.email,
            "full_name": user.full_name
        }

        return data



    @classmethod
    def get_token(self, user):
        """ 
        Provide extra claims to token data
        """
        token = super().get_token(user)

        token["email"] = getattr(user, "email", None)
        token["full_name"] = getattr(user, "full_name", None)

        return token

class LogoutSerializer(serializers.Serializer):
    """ 
    A simple logout serializer for validating and blacklisting refresh tokens
    """

    refresh_token = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs: dict) -> str:
        attrs["refresh_token"].strip()

        return attrs

        
