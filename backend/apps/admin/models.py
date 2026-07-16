from django.db import models
from django.conf import settings

import uuid

AUTH_USER_MODEL = settings.AUTH_USER_MODEL

class Support(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open'
        RESOLVED = 'resolved'
        CRITICAL = 'critical'
        CLOSED  = 'closed'

    support_id = models.UUIDField(
        max_length=20, primary_key=True, unique=True, default=uuid.uuid4,
        db_index=True
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    customer = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="opened_support")
    admin = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_support", null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(blank=True, null=True)
    updated_at  = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    
class SupportConversation(models.Model):
    conversation_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, max_length=20, db_index=True
    )
    support = models.OneToOneField(Support, on_delete=models.CASCADE, related_name="conversations")
    created_at =  models.DateTimeField(auto_now_add=True)

class SupportMessage(models.Model):
    message_id = models.UUIDField(
        primary_key=True,default=uuid.uuid4, max_length=20, db_index=True
    )
    
    conversation = models.ForeignKey(SupportConversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_staff = models.BooleanField(default=False)
    features = models.JSONField(default=dict)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation: {self.conversation.pk}: Message: {self.pk}"
    
    class Meta:
        ordering = ('-created_at',)
