from django.contrib import admin

from .models import Referral, ReferralCode


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'created_at']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = [
        'status', 'referrer__profile__display_name', 
        "referred__profile__display_name", 'created_at'
        ]
    
