from django.contrib.auth import get_user_model
from django.conf import settings
from django.template.defaultfilters import date as date_filter

from .models import Bookings

UserModel = get_user_model()
SUPPORT_URL= f"https://skills-4-hire-frobtendwebsite-ld8136i90-finelifeapps-projects.vercel.app/#contact"
from_email = f"Skills4Hire <skills4hire@{settings.DOMAIN}"

def booking_made_payload(customer: UserModel, provider: UserModel, booking: Bookings):
    booking_service = booking.provider_service.first()
    service = booking_service.services.first()
    return {
        "from_email": from_email,
        "email": provider.email,
        "subject": "Booking Notification",
        "provider_name": provider.full_name,
        "client_name": customer.full_name,
        "client_initials": f"{customer.first_name[0]}{customer.last_name[0]}".upper(),
        "booking_id": str(booking.booking_id),
        "service_name": str(service.name) if service else  None,
        "category": str(service.category.name) if service else None,
        "booking_date": booking.created_at,
        "booking_time": date_filter(booking.created_at, "F j, Y"),
        "service_location": booking.location,
        "currency": booking.currency,
        "price": str(booking.price),
        "client_message": booking.requirements,
        "response_window": "48 hours",
        "booking_url": f"{settings.BASE_URL}api/v1/bookings/{str(booking.booking_id)}/",
        "support_url": SUPPORT_URL,
        'template_name': "bookings/booking_made.html"
    }


def accept_booking_payload(customer: UserModel, provider: UserModel, booking: Bookings):
    data = booking_made_payload(
        customer=customer, provider=provider, booking=booking)
    data.update({
        "provider_initials": f"{provider.first_name[0]}{provider.last_name[0]}".upper(),
        "cancelation_period": "24 hours",
        "template_name": "bookings/accept_booking.html", 
        "email": customer.email,
        "subject": "Booking Confirmed"
    })
    
    return data

def reject_booking_payload(rejected_by: UserModel, booking: Bookings):
    is_client = False
    receipient = None
    if rejected_by == booking.customer:
        receipient = booking.provider.profile.user
        is_client = True
    else:
        receipient = booking.customer
        is_client = False
    data = booking_made_payload(
        customer=booking.customer, provider=booking.provider.profile.user,
        booking=booking
    )
    data.update({
        "from_email": from_email, "email": receipient.email, 
        "subject": "Booking_cancelled", 
        "other_party_name": rejected_by.full_name,
        "receipient_name": receipient.full_name,
        "cancelled_by": "client" if is_client else "provider",
        "cancellation_reason": "", "refund_status": "full",
        "rebook_url": f"{settings.BASE_URL}api/v1/profile_search/",
        "dashboard_url": "https://skills-4-hire-frobtendwebsite-ld8136i90-finelifeapps-projects.vercel.app/professional/home/posts",
        "template_name": "bookings/reject_booking.html",
        "cancelled_at": date_filter(booking.cancelled_at, "F j, Y")

    })
    return data
    

    

        
