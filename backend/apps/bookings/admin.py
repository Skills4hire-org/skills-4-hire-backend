from django.contrib import admin

from .models import Bookings, PaymentRequestBooking, BookingAttachments


@admin.register(BookingAttachments)
class BookingAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'attachment_type_booking', 'attachmentURL_booking',
        'booking', 'payment_request', 'created_at'
    ]
    list_select_related = [
        'booking', 'payment_request'
    ]
    
@admin.register(Bookings)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_status', 'customer', 
        'provider', 'price', 'is_active', 
        'start_date', 'end_date', 'created_at'
 
        ]
    search_fields = [
        'booking_status', 'price'
    ]
    list_filter = [
        'booking_status', 'is_active',
        'created_at', 'updated_at'
    ]
    list_select_related = ['customer', 'provider', 
                           'cancelled_by', 'accepted_by']

@admin.register(PaymentRequestBooking)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = [
        'provider', 'customer',
        'booking', 'message', 'amount',
        'payment_type', 'status',
        'requested_at', 'reviewed_at'
    ]
    list_select_related = [
        'provider', 'customer',
        'booking'
    ]
    list_filter = ['status', 'payment_type']
    search_fields = ['status', 'payment_type']

