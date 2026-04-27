from django.db import models

import  uuid

class SkillActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class Category(models.Model):
    """
    Top-level service category (e.g., Web Development, Graphic Design).
    """
    active_manager = SkillActiveManager()
    objects = models.Manager()

    category_id = models.UUIDField(
        primary_key=True, unique=True, db_index=True,
        default=uuid.uuid4,editable=False)

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "skill categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.name:
            self.name.title()
        return super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save()

class Skill(models.Model):
    """
    Global skill registry. Professionals tag their profiles with these.
    """

    active_objects = SkillActiveManager()
    objects = models.Manager()

    skill_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, max_length=500)

    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="skills",
    )

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'skills'
        constraints = [
            models.UniqueConstraint(fields=("category", "name"), name="unique_category_name")
        ]
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name
    
    def clean(self):
        if self.name:
            self.name.title()

        return super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)