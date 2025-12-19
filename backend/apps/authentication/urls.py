from django.urls import path
from apps.authentication.views import (
    RegistrationView,
    AccountVerificationView,
    ResendOtpView,
    PasswordResetRequestView,
    PasswordResetConfirmView
)
from apps.authentication.tests import test_email_service
app_name = "authentication"

urlpatterns = [
    path("test/email/", test_email_service, name="test"),
    path("auth/register/", RegistrationView.as_view(), name="register-view"),
    path("auth/account/verify/", AccountVerificationView.as_view(), name="verify-account"),
    path("auth/account/resend/otp/", ResendOtpView.as_view(), name="resend-otp"),
    path("auth/account/password/reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("auth/account/password/reset/confirm", PasswordResetConfirmView.as_view(), name="password-confirm")
 
    ]
