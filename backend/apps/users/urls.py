from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    base_profile_view,
    ProviderProfileView
)

routers = DefaultRouter()

routers.register(r'profile', ProviderProfileView, basename="profile")


urlpatterns = [
    path("users/profile/base/",  base_profile_view, name="base-profile"),
    path("users/provider/", include(routers.urls))
]