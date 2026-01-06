from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OnboardingView,
    profile_view,
    ProfileReadView,
    switch_role_view
)

routers = DefaultRouter()

routers.register(r"profile", ProfileReadView, basename="profile")


urlpatterns = [
    path("", include(routers.urls)),
    path("profile/me/onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("profile/me/update/", profile_view, name="profile-me"),
    path("profile/role/switch/", switch_role_view, name="switch-role")
]