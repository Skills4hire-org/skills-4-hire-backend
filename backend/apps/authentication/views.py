from .services.registration_service import (
    RegistrationsService
)
from .services.account_verification_service import (
    AccountVerificationService
)

from .services.resend_otp_service import (
    ResendOtpService
)

from .serializers import (
    RegistrationsSerializer,
    AccountVerificationSerializer,
    ResendOtpSerializer,
    PasswordResetConfirmSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer
)
from .utils.helpers import create_otp_for_user
from .helpers import _send_email_to_user, _get_user_by_email, _get_code_intance_or_none, blacklist_outstanding_token
from .utils.template_helpers import genrate_context_for_otp, generate_context_for_password_reset

from rest_framework.views import APIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings


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
            
            return Response(
                {"detail": "Registration successful. Verify your account using the OTP sent to your email", "user_data": {
                    "email": registration_result["email"],
                    "first_name": registration_result["first_name"],
                    "last_name": registration_result["last_name"]
                }},
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
        try:
            verification_service = AccountVerificationService(serializer)
            email, code = verification_service._decode_serializer()
            user = verification_service.get_user(email)

            otp_instance = verification_service.get_otp_instance(user, code)

            verify_account = verification_service._verify_account(otp_instance, user)
            if verify_account:
                return Response(data={"status": "success", "detail": {
                                                    "message": "Account Verification Successful",
                                                    "data": {
                                                        "full_name": user.full_name,
                                                        "pk": user.pk,
                                                    }
                                            }
                                    }, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({
                "detail": f"Account Verification Failed. Error: {exc}"
            }, status=status.HTTP_400_BAD_REQUEST)

class ResendOtpView(APIView):
    http_method_names = ["post"]
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendOtpSerializer


    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            resend_otp_service = ResendOtpService(serializer)

            email = resend_otp_service._decode_serializer()
            user = resend_otp_service.get_user(email)
            code = create_otp_for_user(user)
            context = genrate_context_for_otp(code=code, email=user.email)
            _send_email_to_user(context)

            return Response({"status": "success", "detail": "OTP code sent. check your email address"}, status=status.HTTP_200_OK)
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
            if user.is_deleted:
                return Response({"status": "Failed", "detail": "User account already deactivated"}, status=status.HTTP_400_BAD_REQUEST)
            
            code = create_otp_for_user(user)
            context = generate_context_for_password_reset(code, valid_email, name=user.full_name)
            print(context)
        except Exception:
            raise
        send_email = _send_email_to_user(context)
        if not send_email.get("success"):
            return Response({"status": "Failed", "detail": "email notification Failed"})
        return Response({"status": "success", "detail": {
            "message": "Password reset email sent...",
            "user_data": {
                "used_id": user.pk,
                "user_name": user.full_name
            }
        }})

class PasswordResetConfirmView(APIView):
    http_method_names = ["post"]
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        code = validated_data.get("code")
        password = validated_data.get("password")
        if any([code, password]) is None:
            return Response({"status": "Failed", "detail": "'code' and 'password' are both required for password reset."}, 
            status=status.HTTP_400_BAD_REQUEST)
        code_instance = _get_code_intance_or_none(code.strip())
        user = code_instance.user
        if user and user.is_active:
            user.set_password(password)
            user.save(update_fields=["password"])
        blacklist_outstanding_token(user)
        return Response({ "success": True, "detail": {"message": "Password Reset successful",
                "user_data": {
                    "user_id": user.pk,
                    "email": user.email,
                    "full_name": user.full_name
                }
            },
            
        }, status=status.HTTP_200_OK)

class LoginView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """
    serializer_class = CustomTokenObtainPairSerializer

token_obtain_pair = LoginView.as_view()


class LogOutView(APIView):
    serializer_class = LogoutSerializer 
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context=request)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = serializer.validated_data.get("refresh_token", None)
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()

            return Response({
                "detail": {
                    "message": "Logged out successfully",
                    "user": request.user.email
                }
            }, status= status.HTTP_200_OK)


        except Exception  as exc:
            return Response({
                "detail": {
                    "message": "Error occurred while validating log out sessions",
                    "exceptions": str(exc)
                }
            }, status=status.HTTP_400_BAD_REQUEST)
logout_view = LogOutView.as_view()

