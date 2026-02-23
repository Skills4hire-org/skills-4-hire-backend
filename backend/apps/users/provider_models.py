from django.db import models, transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from autoslug import AutoSlugField

from .base_model import BaseProfile
import uuid 



class ProviderModel(models.Model):
    class ExperienceChoices(models.TextChoices):
        JUNIOR = "JUNIOR", "Junior"
        MID = "MID", "Mid"
        SENIOR = "SENIOR", "Senior",
        EXPERT = "EXPERT" "Expert"

    class Availability(models.TextChoices):
        FULL_TIME ="FULL_TIME", "Full_time"
        PART_TIME = "PART_TIME", "Part_time"
        HYBRID = "HYBRID", "Hybrid"
        CONTRCT = "CONTRCT", "Contract"
        
    provider_id = models.UUIDField(
        max_length=20, 
        primary_key=True, 
        unique=True,
        default=uuid.uuid4,
        db_index=True
    )
    profile = models.OneToOneField(BaseProfile, on_delete=models.CASCADE, related_name="provider_profile")
    occupation = models.CharField(max_length=250, blank=True, null=True)
    headline = models.CharField(max_length=255, blank=True)
    overview = models.TextField(blank=True)

    experience_level  = models.CharField(max_length=20, choices=ExperienceChoices.choices, default=ExperienceChoices.JUNIOR)

    availability = models.CharField(max_length=20, choices=Availability.choices,default=Availability.FULL_TIME)

    min_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    hourly_pay = models.DecimalField(max_digits=10, decimal_places=2, blank=True , null=True)

    features = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    jobs_done = models.PositiveIntegerField(default=0)

    about = models.TextField()
    max_charge = models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True)
    favourite = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"ProviderProfile({self.profile.user.full_name},)"

    
    class Meta:
        verbose_name_plural = "provider_models"
        indexes = [
            models.Index(fields=["availability"], name="availability_idx"),
            models.Index(fields=("is_active", "is_deleted"), name="act_del_idx")

        ]

class Category(models.Model):
    skill_category_id = models.UUIDField(
        max_length=200,
        primary_key=True,
        db_index=True,
        unique=True, 
    )
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=200, unique=True)
    slug = AutoSlugField(populate_from="category", unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        constraints = [
            models.UniqueConstraint(fields=["name", "category"], name="unique_name_category")
        ]

    def __str__(self):
        return f"Category(), "


class ProviderSkills(models.Model):
    class EfficiencyStatus(models.TextChoices):
        BEGINEER = "BEGINEER", "Begineer"
        INTERMIDIATE = "INTERMIDIATE", "Intermidiate"
        EXPERT = "EXPERT", "Expert"

    skill_id = models.UUIDField(max_length=20, primary_key=True, unique=True, default=uuid.uuid4, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="skills", null=True)
    profile = models.ForeignKey(ProviderModel, on_delete=models.CASCADE, related_name="skills")
    efficiency = models.CharField(max_length=20, choices=EfficiencyStatus.choices, default=EfficiencyStatus.BEGINEER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_primary = models.BooleanField(default=False, db_index=True)
    level_of_experience = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    work = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    
    class Meta:
        verbose_name = "provider_skills"
        constraints = [
            models.UniqueConstraint(
                fields=("profile", "category"),
                name="profile_name_contraints"
            )
        ]
        indexes = [
            models.Index(fields=("is_active", "is_deleted"), name="ac_dele_idx"),
        ]

    def __str__(self):
        return f"ProviderSkills({self.profile.profile.user.full_name}: {self.skills.name})"
    
    @method_decorator(transaction.atomic())
    def soft_delete(self):
        if not isinstance(self, ProviderSkills):
            raise ValueError("Invalid request. Not a valid ProviderSkills instance")
        self.is_active = False
        self.is_deleted = True
        self.deleted_at = self.deleted_at if self.deleted_at else timezone.now()
        self.save()
        
    def can_edit(self, user):
        if user == self.profile.profile.user:
            return True
        return False
    

class Service(models.Model):
    service_id = models.UUIDField(max_length=200, primary_key=True, unique=True, db_index=True, default=uuid.uuid4)
    profile = models.ForeignKey(ProviderModel, on_delete=models.CASCADE, related_name="services")

    name = models.CharField(max_length=500, blank=True, null=True)
    description = models.CharField(blank=True)
    min_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Service({self.profile.profile.user.full_name}: {self.name})"
    
    @method_decorator(transaction.atomic())
    def soft_delete(self):
        if not isinstance(self, Service):
            raise ValueError("Invalid request. Not a valid Service instance")
        self.is_active = False
        self.is_deleted = True
        self.deleted_at = self.deleted_at if self.deleted_at else timezone.now()
        self.save()

    class Meta:
        verbose_name = "services"
        constraints = [
            models.UniqueConstraint(fields=["name", "profile"], name="unique_service_constraints")
        ]
        indexes = [
            models.Index(fields=("is_active", "is_deleted"), name="srv_act_del_idx"),
        ]

    def can_edit(self, user):
        provider_profile = getattr(user.profile, "provider_profile")
        if self.profile == provider_profile:
            return True
        else:
            return False
        
    def clean(self):
        if self.name:
            self.name.title()
        super().clean()


class ServiceImage(models.Model):
    image_id = models.UUIDField(max_length=20, primary_key=True, unique=True, db_index=True, default=uuid.uuid4)
    service = models.ManyToManyField(Service, related_name="images")
    image_url = models.URLField(max_length=200, null=True, blank=True)
    image_public_id = models.URLField(max_length=200, null=True, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ServiceImage({self.image_url}, {self.service.name})"
