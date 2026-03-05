import logging

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import F

import uuid

from ..users.provider_models import Category

logger = logging.getLogger(__name__)

User = get_user_model()

class IsActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Post(models.Model):
    """
    A model representing a post in the system.
    handles different types of posts such as general posts, service requests, job postings, and questions.

    """
    class PostType(models.TextChoices):
        GENERAL = "GENERAL", "General"
        SERVICE = "SERVICE", "Service",
        JOB = "JOB",  "Job"

    objects =  models.Manager()
    is_active_objects = IsActiveManager()

    post_id = models.UUIDField(
        max_length=20,
        primary_key=True,
        unique=True,
        default=uuid.uuid4
    )

    post_content = models.TextField(blank=False, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    role = models.CharField(
        max_length=200, 
        choices=User.RoleChoices, 
        null=True, 
        blank=True,
        help_text="User role when creating the post instance"
    )
    
    post_type = models.CharField(
        max_length=200,
        choices=PostType,
        default=PostType.GENERAL,
        null=True,
        blank=False
    )

    amount = models.DecimalField(
        decimal_places=2, 
        max_digits=10, 
        null=True, 
        blank=True
    )
    

    # Boolean fields 
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)

    # TimeStamp 
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=["post_id"], name="post_id_idx"),
            models.Index(fields=["is_active"], name="active_idx"),
            models.Index(fields=["is_deleted"], name="deleted_idx"),
            models.Index(fields=["created_at"], name="date_idx"),
            models.Index(fields=["is_active", "is_deleted"], name="is_deleted_active_idx")
        ]

    def soft_delete(self):
        """
        A method to soft delete a post instance
        """
        if not hasattr(self, "is_deleted"):
            return None
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=("is_deleted", "is_active"))
        return None

    def __str__(self):
        return f"Posts('{self.user.full_name}', {self.is_active})"
    
    
class PostTag(models.Model):
    post_tag_id = models.UUIDField(
        max_length=20,
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
        db_index=True
    )

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_tag")
    service_name = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="post_tag", null=True, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"PostTag({self.post.pk},)"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "service_name"], name="unique_post_tag"
            )
        ]


class CommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, is_deleted=False)

class Comment(models.Model):

    active_objects = CommentManager() # custom manager to ensure that only active objects are returned
    objects = models.Manager() # default manager

    comment_id = models.UUIDField(max_length=20, unique=True, primary_key=True, default=uuid.uuid4, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="replies"
    )

    # content
    message = models.TextField(max_length=5000)

    # booleanfields
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)  


    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["parent"], name="parent_idx"),
            models.Index(fields=["created_at"], name="time_idx"),
            models.Index(fields=["is_active"], name="is_active_idx")
        ]

    def __str__(self):
        return f"{self.__class__}({self.message}, {self.user.full_name if self.user.full_name else 'Anonymous'})"
    
    def soft_delete(self):
        if not hasattr(self, "is_deleted") and not hasattr(self, "is_active"):
            logger.error("required attributes are empty, 'is_active', 'is_deleted'")
            raise ValueError(f"{self.__class__} must have both 'is_deleted' and 'is_active' attribute")

        from django.utils import timezone

        setattr(self, "is_active", False)
        setattr(self, "is_deleted", True)
        setattr(self, "deleted_at", timezone.now())
        self.save(update_fields=["is_active", "is_deleted", "deleted_at"])


    def can_edit(self, user) -> bool:
        if user == self.user:
            return True
        return False
    

class PostAttachment(models.Model):
    " Post attachment list photo, file, videos"

    class Types(models.TextChoices):
        VIDEO = "VIDEO", "Video"
        PHOTO = "PHOTO", "Photo"
        FILE = "FILE", "File"

    post_attachment_id = models.UUIDField(
        max_length=20,
        unique=True,
        primary_key=True,
        default=uuid.uuid4,
        db_index=True
    )

    attachment_type = models.CharField(max_length=200, choices=Types.choices, default=None, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="attachment", blank=True, null=True)
    attachmentURL = models.URLField(max_length=200, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PostAttachment({self.post.pk}, )"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["post"], name="post_idx")
        ]
    

class PostLike(models.Model):

    objects = models.Manager()
    is_active_objects = IsActiveManager()

    postlike_id = models.UUIDField(
        max_length=20,
        unique=True,
        primary_key=True,
        default=uuid.uuid4,
        db_index=True
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"], name="unique_user_post_like"
            )
        ]
        indexes = [
            models.Index(fields=["postlike_id"], name="postlike_id_idx"),
            models.Index(fields=["post"], name="post_like_idx")
        ]
    
    def __str__(self):
        return f"PostLike({self.user.full_name}, {self.post.pk})"


    def soft_delete(self):
        if not hasattr(self, "is_active"):
            raise ValueError("is_active field is required")

        self.is_active = False
        self.save(update_fields=("is_active",))
        return  None
