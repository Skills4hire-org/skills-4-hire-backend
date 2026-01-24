from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from faker import Faker
import random

class Command(BaseCommand):
    help = "Help Populate users Database"
    User = get_user_model()
    faker = Faker()

    def handle(self, *args, **options):
        n_users = 100
        for _ in range(n_users):
            roles = getattr(self.User.RoleChoices, "values")
            user_email = self.faker.email(safe=True)
            password = self.faker.password(length=8)
            self.User.objects.create_user(email=user_email, password=password, 
                                    first_name=self.faker.first_name(), last_name=self.faker.last_name(),
                                    phone=self.faker.phone_number(), active_role=random.choice(roles))
            self.stdout.write(self.style.SUCCESS(f"population data {user_email}: password: {password}"))
        self.stdout.write(self.style.SUCCESS("User data populated successfully!"))


