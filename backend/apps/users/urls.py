from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .profile_avater.urls import avatar_urlpatterns
from .address.urls import address_urlpatterns
from .skills.urls import skills_urlpatterns
from .services.urls import service_urlpatterns
from .views.onboard import OnboardViewSet
from .views.profile_management import ProfileViewSet, ProfileSearchView

routers = DefaultRouter()

routers.register("onboard", OnboardViewSet, basename="onboard")
routers.register("profile", ProfileViewSet, basename="profile")
routers.register("profile_search", ProfileSearchView, basename="search")

urlpatterns = [
    path("", include(routers.urls)),

]

urlpatterns.extend(avatar_urlpatterns)
urlpatterns.extend(address_urlpatterns)
urlpatterns.extend(skills_urlpatterns)
urlpatterns.extend(service_urlpatterns)