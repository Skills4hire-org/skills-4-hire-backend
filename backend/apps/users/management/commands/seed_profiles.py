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
        users = self.User.objects.filter(is_active=True)[:50]
        base_profile_list = []
        provider_profile_list = []
        customer_profile_list = []

        for user in users:
            base_profile = None
            if BaseProfile.objects.filter(user=user).exists():
                base_profile = BaseProfile.objects.get(user=user)
            else:
                base_profile = BaseProfile(user=user, gender=random.choice(gender_choices),
                                       bio=self.faker.texts())
                base_profile_list.append(base_profile)

            if user.is_provider:
                provider_profile = None
                if ProviderModel.objects.filter(profile=base_profile).exists():
                    provider_profile = None
                else:
                    provider_profile = ProviderModel(profile=base_profile)
                    provider_profile_list.append(provider_profile)

            elif user.is_customer:
                customer_profile = None
                if CustomerModel.objects.filter(profile=base_profile).exists():
                    customer_profile = None
                else:
                    customer_profile = CustomerModel(profile=base_profile)
                    customer_profile_list.append(customer_profile)

        BaseProfile.objects.bulk_create(base_profile_list)
        ProviderModel.objects.bulk_create(provider_profile_list)
        CustomerModel.objects.bulk_create(customer_profile_list)

        self.stdout.write(self.style.SUCCESS("Successfully populated profile for both users and skilled professionals"))
        
