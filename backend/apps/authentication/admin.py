from django.contrib import admin

from .models import CustomUser

@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "is_verified", "is_active", "created_at", "last_login")
    search_fields = ("email",)
