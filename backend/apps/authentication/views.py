from .services.registration_service import (
    RegistrationsService
)
from .serializers import (
    RegistrationsSerializer,
    AccountVerificationSerializer,
    ResendOtpSerializer,
    PasswordResetConfirmSerializer,
    CustomTokenObtainPairSerializer,
    CustomLogoutSerializer
)
from .utils.helpers import create_otp_for_user
from .helpers import (
    _send_email_to_user,
    _get_user_by_email, 
    _get_code_intance_or_none, 
    blacklist_outstanding_token,
    verify_account
)
from .utils.template_helpers import (
    genrate_context_for_otp, 
    generate_context_for_password_reset
)

from rest_framework.views import APIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings
from django.db import transaction

BASE_URL = getattr(settings, "BASE_URL")

class RegistrationView(APIView):
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

    def post(self, request, *args, **kwargs):
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

        serializer = self.serializer_class(data=request.data)

        try:
            registrations_service = RegistrationsService(serializer)
            registration_result = registrations_service.register_service()
            return Response({
                    "status": "success",
                    "detail": "Registration successful. Verify your account using the OTP sent to your email"},
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return Response(
                {"detail": f"Registration failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class AccountVerificationView(APIView):
    http_method_names = ["post"]
    permission_classes = [permissions.AllowAny]
    serializer_class = AccountVerificationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        code = validated_data["code"]
        try:
            code_instance = _get_code_intance_or_none(code)
            account_verifed = verify_account(code_instance=code_instance, user=code_instance.user)
        except Exception:
            return Response({
                "status": "failed", "detail": "account verification Faiiled"}, 
                status=status.HTTP_400_BAD_REQUEST)
        if account_verifed:
            return Response({
                "status": "success", "detail": "Account verification successfull"}, 
                status=status.HTTP_200_OK)

class ResendOtpView(APIView):
    http_method_names = ["post"]
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendOtpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data["email"]
        try:
            user = _get_user_by_email(email)
            code = create_otp_for_user(user)
            context = genrate_context_for_otp(code=code, email=user.email)
            _send_email_to_user(context)
            return Response(
                {"status": "success", "detail": "OTP code sent. check your email address"}, 
                status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({
                "detail": f"Error sending OTP: {exc}"
            }, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    http_method_names = ["post"]
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendOtpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        valid_email = serializer.validated_data.get("email")
        try:
            user = _get_user_by_email(valid_email)
            code = create_otp_for_user(user)
            context = generate_context_for_password_reset(code, valid_email, name=user.full_name)
        except Exception:
            raise
        send_email = _send_email_to_user(context)
        if not send_email.get("success"):
            return Response({"status": "Failed", "detail": "email notification Failed"})
        return Response(
            {"status": "success", "detail": {"message": "Password reset email sent..."}}, 
            status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    http_method_names = ["post"]
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        code, password = validated_data["code"], validated_data["password"]
        try:
            code_instance = _get_code_intance_or_none(code)
            user = code_instance.user
            with transaction.atomic():
                user.set_password(password)
                user.save(update_fields=["password"])

            blacklist_outstanding_token(user)
        except Exception as e:
            return Response(
                {"status": "failed", "detail": f"Error while updating password {e}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {"status": "success", "detail": "Successfully  updated user password"},
            status=status.HTTP_200_OK
        )

class LoginView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """
    serializer_class = CustomTokenObtainPairSerializer

token_obtain_pair = LoginView.as_view()

class LogOutView(APIView):
    serializer_class = CustomLogoutSerializer 
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context=request)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = serializer.validated_data.get("refresh_token", None)
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()

            return Response(
                {"status": "success", "detail": "Logout successful"},
                status=status.HTTP_200_OK
            )


        except Exception  as exc:
            return Response({
                "detail": {
                    "message": "Error occurred while validating log out sessions",
                    "exceptions": str(exc)
                }
            }, status=status.HTTP_400_BAD_REQUEST)
logout_view = LogOutView.as_view()

