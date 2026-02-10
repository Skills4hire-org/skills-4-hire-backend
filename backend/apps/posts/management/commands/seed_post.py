from faker import Faker
import random
import uuid

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from ...models import Post

UserModel = get_user_model()

class Command(BaseCommand):
    help = "Populate Post database"
    faker = Faker()
    posts_types = Post.PostType.values
    users = UserModel.objects.filter(is_active=True)

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Tasks. Post Population"))
        if self.users is None:
            self.stdout.write(self.style.HTTP_NOT_FOUND("User queryset not found"))
            return
        
        if self.posts_types is None:
            self.posts_types = ["GENERAL", "JOB", "SERVICE"]

        amount_of_posts = 5_500
        batches = 700

        temp_post_storage = list()

        for i in range(amount_of_posts):
            self.stdout.write(self.style.NOTICE(f"Creating Post: {i + 1}"))
            post = Post(post_id=uuid.uuid4(), post_content=self.faker.text(max_nb_chars=20),
                        user=random.choice(self.users), post_type=random.choice(self.posts_types),
                        amount=random.randint(1000, 10000), start_date=self.faker.date_time(tzinfo=timezone.get_current_timezone()), 
                        end_date=self.faker.date_time(tzinfo=timezone.get_current_timezone()))
            
            temp_post_storage.append(post)
            if len(temp_post_storage) == batches:
                self.stdout.write(self.style.NOTICE(f"Saving batch of {batches} posts"))
                Post.objects.bulk_create(temp_post_storage)
                temp_post_storage.clear()
        if temp_post_storage:
            self.stdout.write(self.style.NOTICE(f"Saving remaining {len(temp_post_storage)} posts"))
            Post.objects.bulk_create(temp_post_storage)
            temp_post_storage.clear()

