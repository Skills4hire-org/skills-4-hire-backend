
from rest_framework.views import APIView
from apps.authentication.services.registration_service import (
    RegistrationsService
)
from apps.authentication.services.account_verification_service import (
    AccountVerificationService
)

from apps.authentication.services.resend_otp_service import (
    ResendOtpService
)

from apps.authentication.services.password_reset_service import (
    PasswordResetService
)

from apps.authentication.services.password_confirm_service import (
    PasswordConfirmService
)

from apps.authentication.serilaizers import (
    RegistrationsSerializer,
    AccountVerificationSerializer,
    ResendOtpSerializer,
    PasswordResetConfirmSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.authentication.utils.generate_otp import create_otp_for_user, otp_email_for_user
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

            return Response(data={"detail": "Account Verification Successful"}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({
                "detail": f"Account Verification Failed. Error: {exc}"
            }, status=status.HTTP_400_BAD_REQUEST)

class ResendOtpView(APIView):
    http_method_names = ["post"]

    serializer_class = ResendOtpSerializer


    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            resend_otp_service = ResendOtpService(serializer)

            email = resend_otp_service._decode_serializer()
            user = resend_otp_service.get_user(email)

            code = create_otp_for_user(user)

            otp_email_for_user(user, code)

            return Response({"detail": "OTP code sent. check your email address"}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({
                "detail": f"Error sending OTP: {exc}"
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    http_method_names = ["post"]

    serializer_class = ResendOtpSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)

        try:
            password_reset_service = PasswordResetService(serializer)
            user_email = password_reset_service._decode_serializer()

            user = password_reset_service.get_user(user_email)
            generate_token = password_reset_service.generate_token_for_user(user)

            store_token = password_reset_service.cache_token_in_redis_cache(user, generate_token)

            code = create_otp_for_user(user)

            password_reset_service.send_reset_email(code, user)

            return Response({
                "success": True,
                "reset_link": BASE_URL + f"api/v1/auth/account/password/reset/confirm?token={generate_token}"
            })
        except Exception as e:
            return Response({
            "success": False,
            "error messages": f"Error: {e}"
            }
            )

class PasswordResetConfirmView(APIView):
    http_method_names = ["post"]

    serializer_calss = PasswordResetConfirmSerializer
    def post(self, request, *args, **kwargs):

        serializer = self.serializer_calss(data=request.data)

        try:
            password_reset_token = request.query_params.get("token") or request.GET.get("token")

            confirm_service = PasswordConfirmService(serializer)
            confirm_service._validate_serializer()
            
            code, password = confirm_service._decode_serializer()
            user = confirm_service.validate_code(code)

            validate_password_token = confirm_service.pasword_reset_token_check(user, password_reset_token)
            
            if validate_password_token:
                # set user password 

                user.set_password(password)
                user.password = password
                user.save(update_fields=["password"])
            
            confirm_serivice.clean_up_jobs(code, user)

            return Response({
                "success": False,
                "detail": "Password reset successful"
            })
        
        except Exception as exc:
            return Response(
                {
                    "success": False,
                    "detail": f"Error reseting password: {exc}"
                }
            )