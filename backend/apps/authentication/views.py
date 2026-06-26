from .services.registration_service import (
    RegistrationsService
)
from .serializers import (
    RegistrationsSerializer,
    AccountVerificationSerializer,
    ResendOtpSerializer,
    PasswordResetConfirmSerializer,
    CustomTokenObtainPairSerializer,
    CustomLogoutSerializer, SocialAuthSerializer
)
from .utils.helpers import create_otp_for_user
from .helpers import (
    send_email_to_user,
    _get_user_by_email,
    _get_code_instance_or_none,
    blacklist_outstanding_token,
    verify_account
)
from .utils.template_helpers import (
    genrate_context_for_otp, 
    generate_context_for_password_reset,
    genrate_context_for_resend_otp
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.exceptions import api_response, error_response
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings
from django.db import transaction

BASE_URL = getattr(settings, "BASE_URL")

class RegistrationViewSet(viewsets.ModelViewSet):
    """
    Handles registration-related HTTP POST requests.

    This view accepts incoming registration data, validates it using a serializer, 
    and then processes the registration through the associated service class.

    Attributes:
        http_method_names (list): Restricts the view to only accept POST requests.
    """

    http_method_names = ["post"]
    permission_classes = [permissions.AllowAny]


    serializer_class = RegistrationsSerializer

    def create(self, request, *args, **kwargs):
        """
        Handles the POST request to register a new user.

        This method accepts data from the request, validates it using the 
        serializer, and then uses the registration service to process the registration.

        Args:
            request (Request): The HTTP request object containing user registration data.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A Response object with a success or error message.
        """

        serializer = self.get_serializer(data=request.data)

        registrations_service = RegistrationsService(serializer)
        registration_result = registrations_service.register_service()
        return api_response(
            data={
                "create_connection_websocket": f"/ws/user/{registration_result.user_id}/",
            },
            message="Registration successful. Verify your account using the OTP sent to your email",
            status_code=status.HTTP_201_CREATED,
        )

class AccountVerificationViewSet(viewsets.ModelViewSet):
    http_method_names = ["post"]
    permission_classes = [permissions.AllowAny]
    serializer_class = AccountVerificationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        code = validated_data["code"]
        try:
            code_instance = _get_code_instance_or_none(code)
            account_verifed = verify_account(code_instance=code_instance, user=code_instance.user)
        except Exception as e:
            return error_response(
                message=f"Account verification failed: {e}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if account_verifed:
            return api_response(
                data={},
                message="Account verification successful",
                status_code=status.HTTP_200_OK,
            )
        return None

class ResendOtpViewSet(viewsets.ModelViewSet):
    http_method_names = ["post"]
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendOtpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data["email"]
        try:
            user = _get_user_by_email(email)
            if user is None:
                raise NotFound("User not found")
            
            code = create_otp_for_user(user)
            context = genrate_context_for_resend_otp(
                code=code, email=user.email, 
                full_name=user.full_name
                )
            send_email_to_user(context)

            return api_response(
                data={},
                message="OTP code sent. Check your email address",
                status_code=status.HTTP_200_OK,
            )
        
        except Exception as exc:
            return error_response(
                message=f"Error sending OTP: {exc}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

class PasswordResetRequestViewSet(viewsets.ModelViewSet):
    http_method_names = ["post"]
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendOtpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        valid_email = serializer.validated_data.get("email")
        try:
            user = _get_user_by_email(valid_email)
            
            code = create_otp_for_user(user)
            context = generate_context_for_password_reset(code, valid_email, name=user.full_name)
        except Exception:
            raise
        send_email = send_email_to_user(context)
        if not send_email.get("success"):
            return error_response(
                message="Email notification failed",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return api_response(
            data={"message": "Password reset email sent..."},
            message="Password reset email sent",
            status_code=status.HTTP_200_OK,
        )

class PasswordResetConfirmViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    http_method_names = ["post"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        password =  validated_data["password"]
        try:
            code_instance = validated_data["code"]

            user = code_instance.user
            with transaction.atomic():
                user.set_password(password)
                user.save(update_fields=["password"])

                code_instance.is_used = True
                code_instance.is_active = False
                code_instance.save()

            blacklist_outstanding_token(user)
        except Exception as e:
            return error_response(
                message=f"Error while updating password: {e}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        return api_response(
            data={},
            message="Successfully updated user password",
            status_code=status.HTTP_200_OK,
        )

class LoginView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """
    serializer_class = CustomTokenObtainPairSerializer

token_obtain_pair = LoginView.as_view()

class LogOutViewSet(viewsets.ModelViewSet):
    serializer_class = CustomLogoutSerializer 
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = serializer.validated_data.get("refresh_token", None)
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()

            return api_response(
                data={},
                message="Logout successful",
                status_code=status.HTTP_200_OK,
            )


        except Exception as exc:
            return error_response(
                message="Error occurred while validating logout sessions",
                errors={"exceptions": str(exc)},
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class SocialAuthViewSet(viewsets.ModelViewSet):
    http_method_names = ['post']
    serializer_class = SocialAuthSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        data = super().get_serializer_context()
        data['provider'] = self.kwargs.get("provider")
        return data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        return api_response(
            data=response,
            message="Social authentication successful",
            status_code=status.HTTP_201_CREATED,
        )
    
