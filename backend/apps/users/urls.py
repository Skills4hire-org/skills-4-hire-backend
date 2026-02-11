from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .profile_avater.urls import avater_urlpatterns
from .address.urls import address_urlpatterns
from .skills.urls import skills_urlpatterns
from .services.urls import service_urlpatterns

from .views import (
    OnboardingView,
    ProfileViewSet,
    switch_role_view,
)

routers = DefaultRouter()

routers.register(r"profile", ProfileViewSet, basename="profile")


urlpatterns = [
    path("", include(routers.urls)),
    path("onboard/", OnboardingView.as_view(), name="onboarding"),
    path("role/switch/", switch_role_view, name="switch-role")
]

urlpatterns.extend(avater_urlpatterns)
urlpatterns.extend(address_urlpatterns)
urlpatterns.extend(skills_urlpatterns)
urlpatterns.extend(service_urlpatterns)