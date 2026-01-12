from django.db import models
import uuid


class Comment(models.Model):
    comment_id = models.UUIDField(
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
        max_length=20
    )