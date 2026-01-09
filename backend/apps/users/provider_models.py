from django.db import models
from apps.users.base_model import BaseProfile, SkillCategory
import uuid 



class ProviderModel(models.Model):
    """

    """

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
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=True)

    def __str__(self):
        return f"ProviderProfile({self.profile.user.full_name},)"

    
    class Meta:
        verbose_name_plural = "provider_models"
        indexes = [
            models.Index(fields=["availability"], name="availability_idx")

        ]



class ProviderSkills(models.Model):

    class EfficiencyStatus(models.TextChoices):
        BEGINEER = "BEGINEER", "Begineer"
        INTERMIDIATE = "INTERMIDIATE", "Intermidiate"
        EXPERT = "EXPERT", "Expert"

    skill = models.ForeignKey(SkillCategory, on_delete=models.SET_NULL, related_name="skills", null=True)
    profile = models.ForeignKey(ProviderModel, on_delete=models.CASCADE, related_name="skills")

    efficiency = models.CharField(max_length=20, choices=EfficiencyStatus.choices, default=EfficiencyStatus.BEGINEER)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_primary = models.BooleanField(default=False)

    level_of_experience = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "provider_skills"
        constraints = [
            models.UniqueConstraint(
                fields=("profile", "skill"),
                name="profile_name_contraints"
            )
        ]

        