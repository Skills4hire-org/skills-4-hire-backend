from channels.exceptions import AcceptConnection
from django.db import models
from django.contrib.auth import  get_user_model

from apps.posts.models import PostAttachment, IsActiveManager, Post

import uuid

UserModel = get_user_model()



class Conversation(models.Model):

    objects = models.Manager()
    active_objects = IsActiveManager()

    conversation_id = models.UUIDField(
        max_length=20,
        primary_key=True, default=uuid.uuid4,
        editable=False, unique=True)

    sender = models.ForeignKey(
        UserModel, on_delete=models.CASCADE,
        related_name="conversation_sender",  db_index=True)
    receiver = models.ForeignKey(
        UserModel, on_delete=models.CASCADE,
        related_name="conversation_receiver", db_index=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints =  [
            models.UniqueConstraint(
                fields=["sender", "receiver"],
                name="unique_sender_receiver"
            )
        ]
        indexes = [
            models.Index(
                fields=['sender', "receiver"],
                name="send_receive_idx"
            ),
            models.Index(
                fields=["is_active"],
                name='a_idx'
            ),
            models.Index(
                fields=["conversation_id"],
                name="p_idx"
            )
        ]
        db_table = 'conversations'
        verbose_name = "conversation"
        verbose_name_plural = 'conversations'

class Message(models.Model):
    message_id = models.UUIDField(
        max_length=20, primary_key=True,
        unique=True, default=uuid.uuid4,
        editable=False
    )

    objects = models.Manager()
    active_objects = IsActiveManager()

    # attachment for a chat(can be , file, video, image)
    attachment = models.ForeignKey(PostAttachment, on_delete=models.CASCADE, related_name="message")

    sender = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="message")

    message = models.TextField(blank=False, null=False)

    is_active = models.BooleanField(default=True)
    is_edited = models.BooleanField(default=False, db_index=True)
    is_delete = models.BooleanField(default=False,db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'message'
        indexes = [
            models.Index(fields=["is_active"], name="is_active_inx"),
        ]

        verbose_name = "message"

    def __str__(self):
        return  f"Message({self.message_id}, {self.is_active}"

class Negotiations(models.Model):
    negotiations_id = models.UUIDField(
        max_length=20, primary_key=True,
        db_index=True, default=uuid.uuid4,
        editable=False
    )

    class Status(models.TextChoices):
        PENDING = 'PENDING'
        COUNTERED = "COUNTERED"
        ACCEPTED = "ACCEPTED"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="negotiations",db_index=True)
    sender = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="negotiations",db_index=True)

    status = models.CharField(choices=Status.choices, max_length=20, default=Status.PENDING)

    price =  models.DecimalField(decimal_places=2, max_digits=10, blank=False, null=False)

    job_post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name="negotiations",
        blank=True, null=True, db_index=True
    )

    note = models.TextField(blank=True, null=True)
    is_active =  models.BooleanField(default=True)

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True,null=True)

    class Meta:
        verbose_name = "negotiation"
        db_table = "negotiationhistory"
        indexes = [
            models.Index(fields=["is_active"],name="idx_is_active")
        ]

    def __str__(self):
        return f"NegotiationHistory({self.negotiations_id}, {self.is_active}"

