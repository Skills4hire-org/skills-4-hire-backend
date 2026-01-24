from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from ...base_model import BaseProfile
from ...customer_models import CustomerModel
from ...provider_models import ProviderModel

from faker import Faker
import random
import uuid

class Command(BaseCommand):
    help = "Populate user profiles"
    faker = Faker()
    User = get_user_model()

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Populating user profiles..."))
        gender_choices = getattr(BaseProfile.GenderChoices, "values")
        users = self.User.objects.all().filter(is_active=True)
        base_profile_list = []
        for user in users:
            if BaseProfile.objects.filter(user=user).exists():
                continue
            base_profile = BaseProfile(user=user, gender=random.choice(gender_choices), bio=self.faker.texts())
            base_profile_list.append(base_profile)
        BaseProfile.objects.bulk_create(base_profile_list)
        self.stdout.write(self.style.SUCCESS("Successfully Populated base profile db for users"))
        profile_base = BaseProfile.objects.all()
        for profile in profile_base:
            if profile.user.active_role == getattr(self.User.RoleChoices, "CUSTOMER"):
                CustomerModel.objects.create(profile=profile, website=self.faker.url(), total_hires=random.randint(10, 50))
                print("Populated")
            elif profile.user.active_role == getattr(self.User.RoleChoices, "SERVICE_PROVIDER"):
                availability_choices = getattr(ProviderModel.Availability, "values")
                ProviderModel.objects.create(profile=profile, headline=self.faker.text(), occupation=self.faker.job(), 
                                            availability=random.choice(availability_choices))
            else:
                self.stdout.write(self.style.ERROR("Invalid request"))
        self.stdout.write(self.style.SUCCESS("Successfully populated profile for both users and sevice providers"))
        
