from django.contrib import admin

from .models import Wallet, LockedWallet, WalletTransaction, WebhookEvent


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'amount', 'user',
        "type", 'status', 'idempotency_key',
        'reference_key', 'is_active', 'transaction_date',
        'failed_at', 'completed_at', 'updated_at'
    ]

    list_select_related = ['user', 'wallet']


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'event_type', 
        'status', 'error', 'created_at',
        'processed_at'
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