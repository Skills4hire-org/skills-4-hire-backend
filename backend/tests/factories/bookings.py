import factory

from apps.bookings.models import Bookings
from .users import CustomUserFactory, ProviderProfileFactory

class BookingCreateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bookings

    customer = factory.SubFactory(CustomUserFactory)
    provider = factory.SubFactory(ProviderProfileFactory)
    price = 2000

    
