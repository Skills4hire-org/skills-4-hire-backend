from django.core.management import BaseCommand

from ...services.models import Service, ServiceCategory
from ...provider_models import ProviderModel

import faker
import random

faker_instance = faker.Faker()


class Command(BaseCommand):

    help = "populating skilled professionals services"

    def handle(self, *args, **options):

        self.stdout.write(self.style.NOTICE('Starting Task Execution....'))

        message = "populating services to first 10 provider profiles"

        provider_profiles = ProviderModel.objects.all()[:10]
        category = ServiceCategory.objects.all()

        services_list = []
        for profile in provider_profiles:
            for _ in range(10):
                service = Service(profile=profile, name=faker_instance.name(), category=random.choice(category))
                services_list.append(service)

        Service.objects.bulk_create(services_list)
        self.stdout.write(self.style.SUCCESS("Successfully populated services"))
