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
        self.stdout.write(self.style.NOTICE("Populating users"))

        for _ in range(n_users):

            user_email = self.faker.email(safe=True)
            password = self.faker.password(length=8)
            choices = [True, False]

            with open("file.txt", "a") as file:
                file.write(f"\npassword: {password}, email: {user_email}")

            append = ['p', 'c']
            user = self.User.objects.create_user(email=user_email + random.choice(append), password=password,
                                    first_name=self.faker.first_name(), last_name=self.faker.last_name(),
                                    phone=self.faker.phone_number(),
                                    is_active=True, is_verified=True)

            if user.email.endswith("c"):
                user.is_customer = True
            elif user.email.startswith("p"):
                user.is_provider = True
            else:
                user.save()
            user.save()

        self.stdout.write(self.style.SUCCESS("User data populated successfully!"))


