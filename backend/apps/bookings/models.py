from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.forms import ValidationError
from django.utils import timezone

from ..users.provider_models import ProviderModel
from ..users.address.models import UserAddress

import uuid
User = get_user_model()


class Bookings(models.Model):
    class BookingStatus(models.TextChoices):
        PENDING = "Pending"
        FUNDED = 'Funded'
        IN_PROGRESS = 'In_progress'
        COMPLETED = "Completed"
        CANCELLED = "Cancelled"

    booking_id = models.UUIDField(max_length=20, primary_key=True, unique=True, default=uuid.uuid4, db_index=True)
    booking_status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)

    customer = models.ForeignKey(User, on_delete=models.CASCADE,  related_name="bookings")
    provider = models.ForeignKey(ProviderModel, on_delete=models.CASCADE, related_name="bookings")
    address = models.ForeignKey(UserAddress, on_delete=models.CASCADE, related_name="booking_address", blank=True,
                                null=True)

    cancelled_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booking_cancelled", null=True, blank=True)
    accepted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booking_accepted", blank=True,null=True)

    currency = models.CharField(max_length=20, default="NGN")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=True)

    notes = models.TextField(blank=True)
    descriptions = models.TextField()

    requirements = models.TextField(blank=True)

    is_active = models.BooleanField(default=True, db_index=True)

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cancelled_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)

    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Booking"
        constraints = [
            models.UniqueConstraint(fields=("provider", "start_date", "end_date"), name="unique_booking_constraint")
        ]
        indexes = [
            models.Index(fields=("is_active",), name="activ_de_idx"),
        ]

    def __str__(self):
        return f"Booking {self.booking_id} - {self.booking_status}"
    
    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("End date must be after start date.")
        super().clean()

    def is_participants(self, user):
        if user.is_superuser or user.is_staff:
            return True
        if user.profile.provider_profile == self.provider:
            return True
        if user == self.customer:
            return True
        return False

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()

    @transaction.atomic()
    def cancel_booking(self, user):
        if not self.is_participants(user):
            raise ValidationError("Invalid request, can't perform this action")
        self.booking_status = self.BookingStatus.CANCELLED
        self.cancelled_by = user
        self.cancelled_at = timezone.now()
        self.is_active = False
        self.save(update_fields=("booking_status", "cancelled_by", "cancelled_at", 'is_active'))

    def accept_booking(self, user):
        if not self.is_participants(user):
            raise ValidationError("Invalid request, can't perform this action")
        self.booking_status = self.BookingStatus.IN_PROGRESS
        self.accepted_by = user
        self.accepted_at = timezone.now()
        self.save(update_fields=("booking_status", 'accepted_by', 'accepted_at'))

class PaymentRequestBooking(models.Model):

    class RequestStatus(models.TextChoices):
        PENDING = 'PENDING'
        REJECTED = 'REJECTED'
        APPROVED = 'APPROVED'

    class PaymentType(models.TextChoices):
        FULL_TIME = 'FULL_TIME'
        PART_TIME = 'PART_TIME'

    request_id = models.UUIDField(
        primary_key=True, unique=True, editable=False,
        default=uuid.uuid4, db_index=True
    )

    provider = models.ForeignKey(ProviderModel, on_delete=models.CASCADE, related_name='payment_request')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_request_customer')

    booking = models.OneToOneField(Bookings, on_delete=models.CASCADE, related_name='booking_request')

    message = models.TextField(blank=False, null=False, max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices, default=None, blank=False)
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)

    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return f"BookingPaymentRequest {self.request_id}: booking:{self.booking.pk}"

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['requested_at']),
            models.Index(fields=['message'])
        ]

class BookingAttachments(models.Model):
    class Types(models.TextChoices):
        VIDEO = "VIDEO", "Video"
        PHOTO = "PHOTO", "Photo"
        FILE = "FILE", "File"

    attachment_id_booking = models.UUIDField(
        max_length=20,
        unique=True,
        primary_key=True,
        default=uuid.uuid4,
        db_index=True
    )

    attachment_type_booking = models.CharField(max_length=200, choices=Types.choices, default=None, null=True, blank=True)
    attachmentURL_booking = models.URLField(max_length=200, null=True, blank=True)
    booking = models.ForeignKey(
        Bookings, on_delete=models.CASCADE,
        related_name="attachments", null=True, blank=True)

    payment_request = models.ForeignKey(
        PaymentRequestBooking, on_delete=models.CASCADE,
        related_name='attachments_payment_request', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PostAttachment({self.booking.pk}, )"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["attachmentURL_booking"], name="media_idx")
        ]