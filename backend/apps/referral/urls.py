
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ReferralViewSet, ReferralTransactionViewSet

router = DefaultRouter()

router.register("users", ReferralViewSet, basename="referral")
router.register("referral/withdraw", ReferralTransactionViewSet, basename='referral-withdraw')

urlpatterns = [
    path("", include(router.urls))
]