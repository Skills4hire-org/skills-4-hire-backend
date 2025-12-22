from django.urls import path
from apps.authentication.views import (
    RegistrationView,
    AccountVerificationView,
    ResendOtpView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    token_obtain_pair,
    logout_view
)
from apps.authentication.tests import test_email_service
from rest_framework_simplejwt.views import TokenRefreshView


app_name = "authentication"

refresh_view = TokenRefreshView.as_view()

urlpatterns = [
    path("test/email/", test_email_service, name="test"),
    path("auth/account/register/", RegistrationView.as_view(), name="register-view"),
    path("auth/account/verify/", AccountVerificationView.as_view(), name="verify-account"),
    path("auth/account/resend/otp/", ResendOtpView.as_view(), name="resend-otp"),
    path("auth/account/password/reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("auth/account/password/reset/confirm", PasswordResetConfirmView.as_view(), name="password-confirm"),
    path("auth/account/login/", token_obtain_pair, name="token-obtain"),
    path("auth/account/logout/", logout_view, name="logout"),
    path("auth/account/refresh/token/", refresh_view, name="refresh-token")
 
]
