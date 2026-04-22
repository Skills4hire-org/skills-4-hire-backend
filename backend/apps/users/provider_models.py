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
        ENTRY = "entry", _("Entry Level")
        INTERMEDIATE = "intermediate", _("Intermediate")
        EXPERT = "expert", _("Expert")

    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = "available", _("Available")
        PARTIALLY = "partially", _("Partially Available")
        UNAVAILABLE = "unavailable", _("Not Available")
        
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

    min_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_charge = models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True)
    hourly_pay = models.DecimalField(max_digits=10, decimal_places=2, blank=True , null=True)

    years_of_experience =  models.PositiveSmallIntegerField(default=0)

    open_to_full_time = models.BooleanField(
        default=False,
        help_text=_("Willing to convert to full-time employment."),
    )


    is_featured = models.BooleanField(default=False, db_index=True)
    description = models.TextField(blank=True)

    jobs_done = models.PositiveIntegerField(default=0, blank=True, null=True)
    is_top_rated = models.BooleanField(default=False, db_index=True)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"ProviderProfile {self.profile.user.full_name} — {self.professional_title}"

    class Meta:
        verbose_name = _("Professional Profile")
        verbose_name_plural = _("Professional Profiles")
        indexes = [
            models.Index(fields=["availability"]),
            models.Index(fields=["hourly_pay"]),
            models.Index(fields=["jobs_done"]),
            models.Index(fields=["min_charge"]),
            models.Index(fields=["max_charge"]),
            models.Index(fields=["experience_level"]),
            models.Index(fields=["is_top_rated", "is_featured"]),
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
        BEGINNER = "beginner", _("Beginner")
        INTERMEDIATE = "intermediate", _("Intermediate")
        ADVANCED = "advanced", _("Advanced")
        EXPERT = "expert", _("Expert")

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
    years_used = models.PositiveSmallIntegerField(default=0)

    is_primary = models.BooleanField(
        db_index=True,
        default=False,
        help_text=_("Primary skills are highlighted at the top of the profile."),
    )
    sort_order = models.PositiveSmallIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    level_of_experience = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("provider_profile", "skill"), name="unique_provider_skill")
        ]

        ordering = ["-is_primary", "sort_order"]

        indexes = [models.Index(fields=["skill", "proficiency"])]

    def __str__(self):
        return f"ProviderSKills{self.provider_profile.profile.display_name} — {self.skill.name} ({self.proficiency})"

    @method_decorator(transaction.atomic())
    def soft_delete(self):
        if not isinstance(self, ProviderSkill):
            raise ValueError("Invalid request. Not a valid ProviderSkills instance")
        self.is_active = False
        self.save()

