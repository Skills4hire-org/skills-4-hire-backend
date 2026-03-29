from rest_framework.routers import DefaultRouter

from django.urls import path, include
from .views import EndorsementViewSet, EndorsementDetailViewSet

router = DefaultRouter()

router.register("endorsement", EndorsementViewSet, basename="endorse")
router.register("endorsement-detail", EndorsementDetailViewSet, basename="endorse-detail")

endorsement_urlpatterns = [
    path("", include(router.urls))
]