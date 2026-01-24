from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from ...base_model import BaseProfile
from ...customer_models import CustomerModel
from ...provider_models import ProviderModel

from faker import Faker
import random

class Command(BaseCommand):
    help = "Populate user profiles"
    faker = Faker()
    User = get_user_model()

    def handle(self, *args, **options):
        gender_choices = getattr(BaseProfile.GenderChoices, "values")
        users = self.User.objects.all().filter(is_active=True)
        base_profile_list = []
        for user in users:
            base_profile = BaseProfile(user=user, gender=random.choice(gender_choices), bio=self.faker.texts())
            base_profile_list.append(base_profile)
        BaseProfile.objects.bulk_create(base_profile_list)
        self.stdout.write(self.style.SUCCESS("Successfully Populated base profile db for users"))
        for profile in base_profile_list:
            if profile.user.active_role == getattr(self.User.RoleChoice, "CUSTOMER"):
                CustomerModel.objects.create(profile=profile, website=self.faker.url(), total_hires=random.randint(10, 50))
            elif profile.user.active_role == getattr(self.User.RoleChoice, "SERVICE_PROVIDER"):
                availability_choices = getattr(ProviderModel.Availability, "values")
                ProviderModel.objects.create(profile=profile, headline=self.faker.text(), occupation=self.faker.job(), 
                                            availability=random.choice(availability_choices))
            else:
                self.stdout.write(self.style.ERROR("Invalid request"))
        self.stdout.write(self.style.SUCCESS("Successfully populated profile for both users and sevice providers"))
        