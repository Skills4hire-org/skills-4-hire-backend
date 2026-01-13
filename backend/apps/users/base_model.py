from django.db import models
from django.conf import settings
import uuid

class BaseProfile(models.Model):
    """ 
        A Base User profile for storing all user essntial data
    """
    class GenderChoices(models.TextChoices):
         MALE = "MALE", "Male"
         FEMALE = "FEMALE", "Female"
         OTHER = "OTHER", "Other"
         

    profile_id = models.UUIDField(
        max_length=20,
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
        db_index=True
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")

    gender = models.CharField(choices=GenderChoices.choices, max_length=100, blank=True, db_index=True)
    bio = models.TextField(max_length=1000, blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    location = models.CharField(max_length=225)
    is_verified = models.BooleanField(default=False)


    def __str__(self):
        return f"BaseProfile({self.display_name} {self.profile_id})"



class Address(models.Model):
    address_id = models.UUIDField(
        primary_key=True, 
        null=False, 
        unique=True, 
        default=uuid.uuid4,
        db_index=True
    )
    profile = models.ForeignKey(BaseProfile, on_delete=models.CASCADE, related_name="address")
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200,blank=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=255)
    country = models.CharField(max_length=255)

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Address({self.profile.user.full_name}: '{self.state} {self.country}')"


class Avater(models.Model):
    avater_id = models.UUIDField(
        primary_key=True, 
        unique=True,
        null=False, 
        default=uuid.uuid4,
        max_length=20

    )

    profile = models.OneToOneField(BaseProfile, on_delete=models.CASCADE, related_name="avaters")
    avater = models.URLField(
        blank=True,
        null=True,
        max_length=200
        )
    avater_public_id = models.CharField(
        max_length=200,
        null=True, 
        blank=True
    )
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Avater()"


class SkillCategory(models.Model):
    skill_category_id = models.UUIDField(
        max_length=200,
        primary_key=True,
        db_index=True,
        unique=True, 
    )
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SkillCategory(), "