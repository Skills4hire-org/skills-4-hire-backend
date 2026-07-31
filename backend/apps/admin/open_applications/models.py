from django.db import models

import uuid

class ApplicationCategory(models.Model):
    category_id = models.UUIDField(
        primary_key=True, db_index=True, unique=True, default=uuid.uuid4
    )

    name = models.CharField(max_length=266, db_index=True, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class OpenApplications(models.Model):
    application_id = models.UUIDField(
        primary_key=True, unique=True, db_index=True, default=uuid.uuid4
    )
    category = models.ForeignKey(ApplicationCategory, on_delete=models.CASCADE, related_name="applications")

    title = models.CharField(max_length=266, db_index=True)
    description = models.TextField()
    location = models.CharField(max_length=500, null=True, blank=True, db_index=True)
    is_remote = models.BooleanField(default=None)
    job_type = models.CharField(max_length=50, default=None)
    
    company_name = models.CharField(max_length=266)
    job_link = models.URLField(blank=True)

    min_charge = models.DecimalField(decimal_places=2, max_digits=20, null=True)
    max_charge = models.DecimalField(decimal_places=2, max_digits=10, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    upadted_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title




