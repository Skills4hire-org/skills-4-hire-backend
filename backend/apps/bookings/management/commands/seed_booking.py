from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from ...models import Bookings

from faker import Faker
import random

class Command(BaseCommand):
    help = "Populate booking database"

    User = get_user_model()
    faker = Faker()
    def handle(self, *args, **options):
        customers = (self.User.objects.filter(active_role=self.User.RoleChoices.CUSTOMER))
        providers = (self.User.objects.filter(active_role=self.User.RoleChoices.SERVICE_PROVIDER))
        booking_status = getattr(Bookings.BookingStatus, "values")
        n_bookings = 500
        bookings_list = []
        self.stdout.write(self.style.NOTICE("Starting Booking Populations...."))
        for _ in range(n_bookings):
            valid_providers = [getattr(provider.profile, "provider_profile") or getattr(provider.profile, "client_profile") for provider in providers if getattr(provider.profile, "provider_profile") or getattr(provider.profile, "client_profile")]
            bookings = Bookings(booking_status=random.choice(booking_status), customer=random.choice(customers), provider=random.choice(valid_providers),
                                currency=self.faker.currency(), price=random.randint(1000, 10000), notes=self.faker.texts(), description=self.faker.texts(),
                                start_date=timezone.now(), end_date=timezone.now() + timezone.timedelta(days=13))
            
            bookings_list.append(bookings)

            if len(bookings_list) == n_bookings:
                Bookings.objects.bulk_create(bookings_list)
        self.stdout.write(self.style.SUCCESS("Successfully populated booking database."))

