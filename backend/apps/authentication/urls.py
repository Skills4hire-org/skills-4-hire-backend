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
from rest_framework_simplejwt.views import TokenRefreshView


app_name = "authentication"

refresh_view = TokenRefreshView.as_view()

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register-view"),
    path("verify/", AccountVerificationView.as_view(), name="verify-account"),
    path("resend/otp/", ResendOtpView.as_view(), name="resend-otp"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-confirm"),
    path("login/", token_obtain_pair, name="token-obtain"),
    path("logout/", logout_view, name="logout"),
    path("refresh/token/", refresh_view, name="refresh-token")
 
]
