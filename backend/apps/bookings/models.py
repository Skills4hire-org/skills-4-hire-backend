from django.db import models
from django.contrib.auth import get_user_model
from django.forms import ValidationError
from django.utils import timezone

from ..users.provider_models import ProviderModel, Service
from ..users.base_model import Address

import uuid

User = get_user_model()

class Bookings(models.Model):
    class BookingStatus(models.TextChoices):
        PENDING = "PENING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    booking_id = models.UUIDField(max_length=20, primary_key=True, unique=True, default=uuid.uuid4, db_index=True)
    booking_status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)

    customer = models.ForeignKey(User, on_delete=models.CASCADE,  related_name="bookings")
    provider = models.ForeignKey(ProviderModel, on_delete=models.CASCADE, related_name="bookings")  
    service = models.ManyToManyField(Service, related_name="booking_service", blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booking_cancelled", null=True, blank=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name="booking_address", blank=True, null=True)

    currency = models.CharField(max_length=20, default="NGN")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    notes = models.TextField()
    descriptions = models.TextField()
    payment_remark = models.TextField()

    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    is_verified = models.BooleanField(default=True, db_index=True)

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Booking"
        constraints = [
            models.UniqueConstraint(fields=("provider", "start_date", "end_date"), name="unique_booking_constraint")
        ]
        indexes = [
            models.Index(fields=("is_active", "is_deleted"), name="activ_de_idx"),
            models.Index(fields=("is_active", "is_deleted", "is_verified"), name="ve_activ_de_idx"),
        ]

    def __str__(self):
        return f"Booking {self.booking_id} - {self.booking_status}"
    
    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("End date must be after start date.")
        super().clean()

    def soft_delete(self):
        self.is_active = False
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
