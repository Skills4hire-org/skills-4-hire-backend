from django.contrib import admin
from .provider_models import ProviderSkill, ProviderModel
from .customer_models import CustomerModel
from .base_model import BaseProfile
from .services.models import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["profile__profile__display_name", "name",
                    "min_charge", "max_charge", "is_primary",
                    "is_active", "created_at"]
    list_filter = ['is_active']
    search_fields =  ['name']
    list_per_page = 50

@admin.register(BaseProfile)
class BaseProfileManage(admin.ModelAdmin):
    list_display = ['display_name', 'user__is_customer',
                    'user__is_provider', 'gender', 'is_active']
    search_fields = ['display_name']

@admin.register(ProviderModel)
class ProviderModelAdmin(admin.ModelAdmin):
    list_display = ["profile__display_name",
                    "professional_title",
                    "availability",
                    "years_of_experience",
                    "open_to_full_time", 'is_active']

    list_filter = ['is_active', "profile__display_name", "years_of_experience"]
    list_per_page = 50

@admin.register(CustomerModel)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['profile__display_name', "industry_name", 'city', 'is_active']
    list_filter = ['is_active', "profile__display_name"]
    list_per_page = 50