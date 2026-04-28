from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import WalletViewSet, WalletTransactionViewSet
from .payments.views import BankAccountViewSet, TransferViewSet

router = DefaultRouter()

router.register("", WalletViewSet, basename='user_wallet')
router.register('', WalletTransactionViewSet, basename='wallet_transaction')
router.register("bank", BankAccountViewSet, basename='bank')
router.register("transfer/recipient", TransferViewSet, basename='receipient')


urlpatterns = [
    path("", include(router.urls))
]