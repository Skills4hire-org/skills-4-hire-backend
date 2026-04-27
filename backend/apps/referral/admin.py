from django.contrib import admin

from .models import Referral, ReferralCode, ReferralTransactions

@admin.register(ReferralTransactions)
class ReferralTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "amount", "status", "reference_key",
        "idempotency_key", "transfer_code",
        "is_active", 'created_at', 'completed_at',
        "failed_at", "reversed_at"
    ]

@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'created_at']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = [
        'status', 'referrer__profile__display_name', 
        "referred__profile__display_name", 'created_at'
        ]
    
