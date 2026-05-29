from django.db import models, transaction
from django.utils.decorators import method_decorator
from django.utils.text import gettext_lazy as _

from .base_model import BaseProfile
import uuid

from .skills.models import Skill

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class ProviderModel(models.Model):
    class ExperienceLevel(models.TextChoices):
        ENTRY = "ENTRY"
        INTERMEDIATE = "INTERMEDIATE"
        EXPERT = "EXPERT"

    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = "AVAILABLE"
        PARTIALLY = "PARTIALLY"
        UNAVAILABLE = "UNAVAILABLE"
        
    provider_id = models.UUIDField(
        max_length=20, 
        primary_key=True, 
        unique=True,
        default=uuid.uuid4,
        db_index=True
    )

    profile = models.OneToOneField(BaseProfile, on_delete=models.CASCADE,
                                   related_name="provider_profile", db_index=True                             )
    professional_title = models.CharField(max_length=250, blank=False, null=True)
    headline = models.CharField(max_length=255, blank=True, null=True)
    overview = models.TextField(blank=True, null=True)

    experience_level  = models.CharField(max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.ENTRY)
    availability = models.CharField(max_length=20, choices=AvailabilityStatus.choices,default=AvailabilityStatus.PARTIALLY)

    open_to_full_time = models.BooleanField(
        default=False,
        help_text=_("Willing to convert to full-time employment."),
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"ProviderProfile {self.profile.user.full_name} — {self.professional_title}"


    def clean(self):
        if self.professional_title:
            self.professional_title.title()
        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _("Professional Profile")
        verbose_name_plural = _("Professional Profiles")
        indexes = [
            models.Index(fields=["availability"]),
            models.Index(fields=['professional_title'])
        ]

class ProviderSkill(models.Model):
    """
    Junction: Professional & Skill.
    Includes self-reported proficiency.
    """

    active_objects = ActiveManager()
    objects =  models.Manager()

    class Proficiency(models.TextChoices):
        BEGINNER = "BEGINNER"
        INTERMEDIATE = "INTERMEDIATE"
        ADVANCED = "ADVANCED"
        EXPERT = "EXPERT"

    provider_skill_id = models.UUIDField(
        primary_key=True, db_index=True, editable=False,
        unique=True, default=uuid.uuid4)

    provider_profile = models.ForeignKey(
        ProviderModel,
        on_delete=models.CASCADE,
        related_name="skills",
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="provider_skills",
    )

    proficiency = models.CharField(
        max_length=20,
        choices=Proficiency.choices,
        default=Proficiency.INTERMEDIATE,
    )

    years_used = models.PositiveSmallIntegerField(default=0, blank=True)

    is_primary = models.BooleanField(
        db_index=True,
        default=False,
        help_text=_("Primary skills are highlighted at the top of the profile."),
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("provider_profile", "skill"), name="unique_provider_skill")
        ]

        indexes = [models.Index(fields=["skill", "proficiency"])]

    def __str__(self):
        return f"ProviderSKills{self.provider_profile.profile.display_name} — {self.skill.name} ({self.proficiency})"

    @method_decorator(transaction.atomic())
    def soft_delete(self):
        if not isinstance(self, ProviderSkill):
            raise ValueError("Invalid request. Not a valid ProviderSkills instance")
        self.is_active = False
        self.save()

