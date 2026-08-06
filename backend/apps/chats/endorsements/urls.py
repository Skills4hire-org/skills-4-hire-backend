from rest_framework.routers import DefaultRouter

from django.urls import path, include
from .views import EndorsementViewset

router = DefaultRouter()

router.register("endorsement", EndorsementViewset, basename="endorse")

endorsement_urlpatterns = [
    path("", include(router.urls))
]