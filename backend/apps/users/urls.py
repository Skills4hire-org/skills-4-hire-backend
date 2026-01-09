from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OnboardingView,
    profile_view,
    ProfileReadView,
    switch_role_view,
    AddressViewSet
)

routers = DefaultRouter()

routers.register(r"", ProfileReadView, basename="profile")
routers.register(r"address", AddressViewSet, basename="address")


urlpatterns = [
    path("profile/", include(routers.urls)),
    path("profile/me/onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("profile/me/update/", profile_view, name="profile-me"),
    path("profile/role/switch/", switch_role_view, name="switch-role")
]