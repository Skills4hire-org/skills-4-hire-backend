from django.db import models
from django.contrib.auth import get_user_model

from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework.exceptions import ValidationError

from ..users.provider_models import ProviderModel

import uuid
import logging

from ..users.customer_models import CustomerModel

logger = logging.getLogger(__name__)
UserModel = get_user_model()

class ProfileReview(models.Model):

    """ Profile review for skilled professionals and customers """

    review_id = models.UUIDField(
        max_length=20,
        primary_key=True,
        default=uuid.uuid4,
        db_index=True
    )
    customer_profile = models.ForeignKey(
        CustomerModel, on_delete=models.CASCADE,
        related_name='reviews', null=True, blank=True)
    provider_profile = models.ForeignKey(
        ProviderModel, on_delete=models.CASCADE,
        related_name="reviews", null=True, blank=True
    )

    reviewed_by = models.ForeignKey(
        UserModel, on_delete=models.SET_NULL,
        related_name="reviews", null=True
    )

    review = models.TextField(null=True, blank=False)

    is_active = models.BooleanField(default=True)

    # Timestamp 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ratings_review"
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"], name="active_deleted_idx"),
            models.Index(fields=["created_at"], name="d_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["reviewed_by", "customer_profile"], name="unique_review_profile_customer"),
            models.UniqueConstraint(fields=['reviewed_by', 'provider_profile'], name="unique_user_profile"),
        ]
    def __str__(self):
        return f"Review {self.review_id}  created: {self.created_at}"

    def clean(self):
        if self.customer_profile is not  None:
            if self.reviewed_by == self.customer_profile.profile.user:
                raise ValidationError("You cannot review for yourself")

            if self.pk is None:
                already_rated = ProfileReview.objects.filter(
                    reviewed_by=self.reviewed_by,
                    customer_profile=self.customer_profile
                ).exists()

                if already_rated:
                    raise ValidationError("You already rated this profile")

        elif self.provider_profile is not None:
            if self.reviewed_by == self.provider_profile.profile.user:
                raise ValidationError("You cannot review for your self.")

            if self.pk is None:
                already_rated = ProfileReview.objects.filter(
                    reviewed_by=self.reviewed_by,
                    provider_profile=self.provider_profile
                ).exists()
                if already_rated:
                    raise ValidationError("You already reviewed this Profile")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def soft_delete(self):
        if hasattr(self, "is_active"):
            setattr(self, "is_active", False)

        self.save(update_fields=['is_active'])

    def is_able_modify(self, user):
        if self.reviewed_by == user:
            return True
        if user.is_superuser or user.is_staff:
            return True
        return False

class ProfileRating(models.Model):
    rating_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        max_length=20,
        db_index=True
    )

    customer_profile = models.ForeignKey(
        CustomerModel, on_delete=models.CASCADE,
        related_name='ratings', null=True, blank=True)

    provider_profile = models.ForeignKey(
        ProviderModel, on_delete=models.CASCADE,
        related_name="ratings", null=True, blank=True
    )
    rate_by = models.ForeignKey(
        UserModel, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="ratings")

    rating = models.PositiveIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(5)
    ], blank=False)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rating {self.rating_id} created: {self.created_at}"

    def clean(self):
        if self.customer_profile is not None:
            if self.rate_by == self.customer_profile.profile.user:
                raise ValidationError("You cannot rate for yourself")

            if self.pk is None:
                already_rated = ProfileReview.objects.filter(
                    rate_by=self.rate_by,
                    customer_profile=self.customer_profile
                ).exists()

                if already_rated:
                    raise ValidationError("You already rated this profile")

        elif self.provider_profile is not None:
            if self.rate_by == self.provider_profile.profile.user:
                raise ValidationError("You cannot rate for your self.")

            if self.pk is None:
                already_rated = ProfileRating.objects.filter(
                    reviewed_by=self.rate_by,
                    provider_profile=self.provider_profile
                ).exists()
                if already_rated:
                    raise ValidationError("You already rated this Profile")

    def soft_delete(self):
        if hasattr(self, "is_active"):
            setattr(self, "is_active", False)
        self.save(update_fields=["is_active"])

    def is_able_modify(self, user):
        if self.rate_by == user:
            return True
        if user.is_superuser and user.is_staff:
            return True
        return False
    
    class Meta:
        db_table = "ratings_ratings"
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"

        indexes = [
            models.Index(fields=['is_active'], name="ra_act_idx"),
            models.Index(fields=['created_at'], name="dat_idx"),
            models.Index(fields=['rate_by'], name='rated_by_idx')
        ]
        constraints = [
            models.UniqueConstraint(fields=['rate_by', "customer_profile"], name='rate_profile_unique_customer'),
            models.UniqueConstraint(fields=['rate_by', "provider_profile"], name='rate_profile_unique_provider')
        ]

