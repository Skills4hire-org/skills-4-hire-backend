from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    onboarding_view,
    profile_view,
    ProfileReadView
)

routers = DefaultRouter()

routers.register(r"profile", ProfileReadView, basename="profile")
urlpatterns = [
    path("", include(routers.urls)),
    path("profile/onboarding/", onboarding_view, name="onboarding"),
    path("profile/me/update", profile_view, name="profile-me")
]