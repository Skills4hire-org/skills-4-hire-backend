from django.urls import path, include
from .views import (
    RegistrationView,
    AccountVerificationViewSet,
    ResendOtpViewSet,
    PasswordResetRequestViewSet,
    PasswordResetConfirmViewSet,
    token_obtain_pair,
    LogOutViewSet
)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register("verify", AccountVerificationViewSet, basename="account_verify")
router.register("resend/otp", ResendOtpViewSet, basename="otp_resend")
router.register("password/reset", PasswordResetRequestViewSet, basename="password_reset")
router.register("password/reset/confirm", PasswordResetConfirmViewSet, basename="password_reset_confirm")
router.register("logout", LogOutViewSet, basename="logout")


app_name = "authentication"

refresh_view = TokenRefreshView.as_view()

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register-view"),
    path("login/", token_obtain_pair, name="token-obtain"),
    path("refresh/token/", refresh_view, name="refresh-token"),
    path("", include(router.urls)),
]
