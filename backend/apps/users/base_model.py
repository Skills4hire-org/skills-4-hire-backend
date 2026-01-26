from django.db import models, transaction
from django.conf import settings
from django.utils import timezone 
from django.utils.decorators import method_decorator  

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
    bio = models.TextField(max_length=10000, blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    location = models.CharField(max_length=225)
    is_verified = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"BaseProfile({self.display_name} {self.profile_id})"

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=("is_active", "is_deleted"), name="is_d_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.user.full_name if self.user.full_name else self.user.first_name
        super().save(*args, **kwargs)


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

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def soft_delete(self):
        if not isinstance(self, Address):
            raise ValueError("Invalid request. Not a valid address instance")
        self.is_active = False
        self.is_deleted = True
        self.deleted_at = self.deleted_at if self.deleted_at else timezone.now()
        self.save()

    def __str__(self):
        return f"Address({self.profile.user.full_name}: '{self.state} {self.country}')"

    def can_edit(self, user):
        if user == self.profile.user:
            return True
        return False

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["profile", "postal_code"], name="unique_name_postal_code_constraints")
        ]
    
class Avater(models.Model):
    avater_id = models.UUIDField(primary_key=True, unique=True, null=False, default=uuid.uuid4, max_length=20)
    profile = models.OneToOneField(BaseProfile, on_delete=models.CASCADE, related_name="avater")
    avater = models.URLField(blank=True, null=True, max_length=200)
    avater_public_id = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Avater()"
    
    @method_decorator(transaction.atomic())
    def soft_delete(self):
        if not isinstance(self, Avater):
            raise ValueError("Invalid request. Not a valid Avater instance")
        self.avaters = None
        self.avater_public_id = None
        self.description = None
        self.is_active = False
        self.is_deleted = True
        self.deleted_at = self.deleted_at if self.deleted_at else timezone.now()
        self.save()

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