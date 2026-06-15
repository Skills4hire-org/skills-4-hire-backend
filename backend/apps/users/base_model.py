from django.db import models
from django.conf import settings
import uuid


class BaseProfile(models.Model):
    """ 
        A Base User profile for storing all user essential data, both customer and service professionals share this profile
    """
    class GenderChoices(models.TextChoices):
        MALE = "MALE"
        FEMALE = "FEMALE"
        OTHER = "OTHER"

    profile_id = models.UUIDField(
        max_length=20,
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
        db_index=True
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")

    gender = models.CharField(choices=GenderChoices.choices, max_length=100, blank=True, db_index=True)
    bio = models.TextField(max_length=10000, blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    years_of_experience = models.IntegerField(blank=True, null=True, db_index=True)
    place_of_work = models.CharField(max_length=255, blank=True, null=True)

    # Contact info: optional fields for phone and location, used for relevance and trust scoring
    phone_number = models.CharField(max_length=50, blank=True, null=True)   
    cover_photo = models.JSONField(default=dict)

    nin = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)
    drivers_lisence = models.JSONField(name="drivers_lisence", default=dict)
    passport = models.JSONField(name="passport", default=dict)
    certificates = models.JSONField(name="certificates", default=list)
    # optional field for date of birth
    date_of_birth = models.DateField(blank=True, null=True)

    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    # Trust score: computed from completed jobs, ratings, and endorsements
    # Normalized to 0.0-1.0 range. This is the most important ranking signal.
    trust_score = models.FloatField(default=0.0, db_index=True)
    
    # Location: composite field used for relevance matching in recommendations
    location = models.CharField(max_length=200, blank=True, null=True, help_text="User's primary location for relevance scoring")

    category_interest = models.ManyToManyField("users.ServiceCategory", blank=True, related_name="interested_profiles", help_text="User's primary service category interest for relevance scoring")

    # is_active_user: flag to mark recently active users for feed ranking boost
    is_active_user = models.BooleanField(default=True, db_index=True, help_text="User is actively engaging with the platform")
    
    # last_active: updated on login or post interaction; used to compute is_active_user
    last_active = models.DateTimeField(blank=True, null=True, help_text="Last time user logged in or interacted with content")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True, db_index=True)
    is_certified = models.BooleanField(default=False, db_index=True)

    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"BaseProfile({self.display_name} {self.profile_id})"

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=("is_active",), name="is_d_idx"),
            models.Index(fields=("trust_score",), name="trust_score_idx"),
            models.Index(fields=("is_active_user",), name="is_active_user_idx"),
            models.Index(fields=("last_active",), name="last_active_idx"),
            models.Index(fields=("is_certified",), name="is_certified_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.user.full_name if self.user.full_name else self.user.first_name
        super().save(*args, **kwargs)

    
class WorkImages(models.Model):
    """ 
        A model to store work images for service professionals, linked to the BaseProfile
    """
    profile = models.ForeignKey(BaseProfile, on_delete=models.CASCADE, related_name="work_images")
    image_url = models.URLField(max_length=200, blank=True, null=True)
    public_id = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"WorkImage({self.profile.display_name} - {self.description})"

    class Meta:
        ordering = ["-created_at"]