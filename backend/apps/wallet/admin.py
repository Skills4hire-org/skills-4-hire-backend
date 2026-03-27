from django.contrib import admin

from .models import Wallet, LockedWallet
from .transactions.models import Transactions

@admin.register(Transactions)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'booking', 'sender',
        'receiver', 'amount',
        'type', 'status', 'reference_key',
        'is_active', 'transaction_date'
    ]

    list_filter = [
        'status', 'type', 'is_active',
        'transaction_date'
    ]


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        'balance', 'is_active', 
        'created_at', 'user'
    ]
    list_editable = ['is_active']

    list_select_related = ['user']


@admin.register(LockedWallet)
class LockWalletAdmin(admin.ModelAdmin):
    list_display = [
        'booking', 'user_wallet',
        'is_released', 'amount',
        'locked_at'
    ]

    list_select_related = [
        'booking', 'user_wallet'
    ]
    search_fields = ['is_released']
    list_filter = ['is_released']