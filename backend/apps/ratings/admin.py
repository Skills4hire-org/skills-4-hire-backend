from django.contrib import admin

from .models import ProfileReview

@admin.register(ProfileReview)
class ProfileReviewAdmin(admin.ModelAdmin):
    list_display = [
        "reviewed_by__profile__display_name",
        "ratings", "reviews", "provider_profile__profile__display_name",
        "created_at"
    ]
