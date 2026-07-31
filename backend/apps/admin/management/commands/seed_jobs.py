from faker import Faker
from django.core.management.base import BaseCommand
from django.db import transaction

import random
from ...open_applications.models import OpenApplications, ApplicationCategory


class Command(BaseCommand):
    help = "Populate Category and Open job application database with realistic fake data"

    def handle(self, *args, **options):
        self.faker = Faker()
      
        amount_of_jobs = 1000
        self.stdout.write(self.style.MIGRATE_HEADING(f"Starting execution: Generating {amount_of_jobs} jobs..."))

        elements=["Information Technology", "Healthcare", "Finance", "Education", "Marketing", "Sales"]
        application = []
        jobs = []
        with transaction.atomic():
            for name in elements:
                app = ApplicationCategory(name=name, description=self.faker.text(max_nb_chars=50))
                application.append(app)
            ApplicationCategory.objects.bulk_create(application)
            self.stdout.write(self.style.NOTICE(f"Successfully bulk saved {len(application)} job category."))
            application.clear()

            open_application = ApplicationCategory.objects.all()

            for i in range(amount_of_jobs):
                min_amt = round(random.uniform(20.00, 100.00), 2)
                max_amt = round(random.uniform(min_amt, min_amt + 100.00), 2)
                    
                job = OpenApplications(
                    title=self.faker.job()[:266], description=self.faker.text(max_nb_chars=1000),
                    location=self.faker.city() if random.choice([True, False]) else None,
                    is_remote=self.faker.boolean(),
                    job_type=random.choice(["Full-time", "Part-time", "Contract", "Freelance"]),
                    company_name=self.faker.company()[:266],
                    job_link=self.faker.url() if random.choice([True, False]) else "",
                    min_charge=str(min_amt),
                    max_charge=str(max_amt),
                    category=random.choice(open_application)
                )
                jobs.append(job)
            OpenApplications.objects.bulk_create(jobs)
            self.stdout.write(self.style.NOTICE(f"Successfully bulk saved {len(jobs)} jobs."))
            jobs.clear()

            self.stdout.write(self.style.SUCCESS("All tasks finished successfully!"))

                        

