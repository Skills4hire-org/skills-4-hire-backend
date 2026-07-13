import random
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from faker import Faker
from ...models import Post, Comment

UserModel = get_user_model()

class Command(BaseCommand):
    help = "Populate Post and Comment database with realistic fake data"

    def handle(self, *args, **options):
        faker = Faker()
        users = UserModel.objects.all()
        
        if not users.exists():
            self.stdout.write(self.style.ERROR("No users found in the database. Please create users first."))
            return

        try:
            post_types = Post.PostType.values
        except AttributeError:
            post_types = ["GENERAL", "JOB", "SERVICE"]

        amount_of_posts = 5500
        batch_size = 700
        temp_post_storage = []

        self.stdout.write(self.style.MIGRATE_HEADING(f"Starting execution: Generating {amount_of_posts} posts..."))

        with transaction.atomic():
            for i in range(amount_of_posts):
                # Generate logical start and end dates
                start = faker.date_time_between(start_date="-30d", end_date="now", tzinfo=timezone.get_current_timezone())
                end = faker.date_time_between(start_date="now", end_date="+30d", tzinfo=timezone.get_current_timezone())
                
                post_content = f"{faker.catch_phrase()}! {faker.paragraph(nb_sentences=3)}"

                post = Post(
                    post_id=uuid.uuid4(),
                    post_content=post_content,
                    user=random.choice(users),
                    post_type=random.choice(post_types),
                    amount=random.randint(1000, 10000),
                    start_date=start,
                    end_date=end
                )
                temp_post_storage.append(post)

                # Batch save posts
                if len(temp_post_storage) == batch_size:
                    Post.objects.bulk_create(temp_post_storage)
                    self.stdout.write(self.style.NOTICE(f"Successfully bulk saved {len(temp_post_storage)} posts."))
                    temp_post_storage.clear()

            # Save remaining posts
            if temp_post_storage:
                Post.objects.bulk_create(temp_post_storage)
                self.stdout.write(self.style.NOTICE(f"Successfully bulk saved remaining {len(temp_post_storage)} posts."))
                temp_post_storage.clear()

        # Comment Generation Section
        comments_per_post = 15 # Reduced from 700 to keep database size healthy, change back if needed
        sampled_posts = Post.objects.all()[:100]
        comment_storage = []

        self.stdout.write(self.style.MIGRATE_HEADING(f"Starting execution: Generating comments for {len(sampled_posts)} posts..."))

        with transaction.atomic():
            for post in sampled_posts:
                for _ in range(comments_per_post):
                    comment = Comment(
                        user=random.choice(users),
                        post=post,
                        message=faker.sentence(nb_words=12) # Reasonable comment length
                    )
                    comment_storage.append(comment)
                
                # Bulk insert comments per post to keep memory clear
                Comment.objects.bulk_create(comment_storage)
                comment_storage.clear()
                
            self.stdout.write(self.style.SUCCESS("All tasks finished successfully!"))
