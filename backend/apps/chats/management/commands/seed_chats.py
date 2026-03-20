import random

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q

from faker import Faker

from ...models import Conversation, Message, Negotiations

faker_instance = Faker()
UserModel = get_user_model()

class Command(BaseCommand):
    help = "Populate chat box"


    def handle(self, *args, **options):
        global faker_instance
        global UserModel

        users = UserModel.objects.filter(is_active=True, is_verified=True)

        halves = int(len(users) / 2)

        first_batch = users[:halves]
        second_batch = users[halves:]

        self.stdout.write(self.style.NOTICE("Starting Task..."))
        for user in first_batch:
            partner = random.choice(second_batch)

            if Conversation.active_objects.filter(
                Q(participant_one=user, participant_two=partner)|
                Q(participant_one=partner, participant_two=user)
            ):
                self.stdout.write(self.style.NOTICE(f"Conversation Exists Between {user.email} <-> {partner.email}"))
                continue
            else:
                self.stdout.write(self.style.NOTICE(f"Seeding Task {user.email} <-> {partner.email}"))
                Conversation.objects.create(
                    participant_one=user, participant_two=partner
                )
        self.stdout.write(self.style.SUCCESS("Success in Conversation Population.."))

        messages = 10
        user = []
        for _ in range(messages):
            first_user = random.choice(first_batch)
            second_user = random.choice(second_batch)
            conversation = Conversation.objects.get(
                Q(participant_one=first_user, participant_two=second_user)|
                Q(participant_one=second_user, participant_two=first_user)
            )
            user = [first_user, second_user]
            if conversation is None:
                continue

            # send message to this conversation
            sender = random.choice(user)
            self.stdout.write(self.style.NOTICE(f"Sending Message: {sender.email} -> Conversation {conversation.pk}"))
            Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=faker_instance.text(max_nb_chars=100)
            )
        self.stdout.write(self.style.SUCCESS("Success Sending Message!"))