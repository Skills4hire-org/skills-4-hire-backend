from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import WalletViewSet, WalletTransactionViewSet

router = DefaultRouter()
router.register("", WalletViewSet, basename='user_wallet')
router.register('', WalletTransactionViewSet, basename='wallet_transaction')


urlpatterns = [
    path("", include(router.urls))
]