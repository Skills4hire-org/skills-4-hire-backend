import pytest
import random

from ....factories import BookingCreateFactory
from apps.bookings.models import Bookings


@pytest.fixture
def create_booking(db, customer, provider_profile):
    return BookingCreateFactory(customer=customer,
                                provider=provider_profile)


@pytest.fixture
def booking_with_services(db, create_booking, provider_service):
    create_booking.service.add(provider_service)
    return create_booking

@pytest.fixture
def create_multiple_bookings(db, another_customer, customer, provider_profile):
    bookings = []
    status_choices = Bookings.BookingStatus.values
    for _ in range(5):
        booking = BookingCreateFactory(
            customer=customer, 
            provider=provider_profile,
            booking_status=random.choice(status_choices))
    
        bookings.append(booking)
    
    for _ in range(5):
        booking = BookingCreateFactory(
            customer=another_customer, 
            provider=provider_profile,
            booking_status=random.choice(status_choices))
    
        bookings.append(booking)
    
    return bookings

