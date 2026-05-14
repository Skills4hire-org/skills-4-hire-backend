import logging

from django.db import models
from django.contrib.auth import get_user_model

import uuid

from ..users.address.models import UserAddress
from ..users.services.models import ServiceCategory

logger = logging.getLogger(__name__)

User = get_user_model()

class IsActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Post(models.Model):
    """
    A model representing a post in the system.
    handles different types of posts such as general posts, service requests, job postings.

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

    post_title = models.CharField(max_length=500, blank=False,null=True)

    tags = models.ManyToManyField(ServiceCategory, related_name="tags", blank=True)
    post_content = models.TextField(blank=False, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts", blank=True, null=True)

    country = models.CharField(max_length=100, blank=True, null=True)   
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

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
    is_reposted = models.BooleanField(default=False, db_index=True)
    is_remote = models.BooleanField(default=False)
    # is_published: Flag to indicate if the post is published and eligible for feed recommendation
    is_published = models.BooleanField(default=True, db_index=True)

    # Engagement tracking: Total count of likes + comments + reposts, updated via signals
    engagement_count = models.PositiveIntegerField(default=0)

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
            models.Index(fields=["is_active", "is_deleted"], name="is_deleted_active_idx"),
            models.Index(fields=["is_published"], name="is_published_idx"),
            models.Index(fields=["engagement_count"], name="engagement_count_idx")
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
    


class CommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, is_deleted=False)

class Comment(models.Model):

    active_objects = CommentManager() # custom manager to ensure that only active objects are returned
    objects = models.Manager() # default manager

    comment_id = models.UUIDField(max_length=20, unique=True, primary_key=True, default=uuid.uuid4, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", null=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="replies"
    )

    # content
    message = models.TextField(max_length=5000, blank=False)
    # boolean fields
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
        return f"{self.__class__.__name__}({self.message}, {self.user.full_name if self.user.full_name else 'Anonymous'})"
    
    def soft_delete(self):
        if not hasattr(self, "is_deleted") and not hasattr(self, "is_active"):
            logger.error("required attributes are empty, 'is_active', 'is_deleted'")
            raise ValueError(f"{self.__class__.__name__} must have both 'is_deleted' and 'is_active' attribute")

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
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="attachments", blank=True, null=True)
    attachmentURL = models.URLField(max_length=200, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="attachments")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PostAttachment({self.post.pk}, )"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["post"], name="post_id")
        ]

class Likes(models.Model):

    objects = models.Manager()
    is_active_objects = IsActiveManager()

    like_id = models.UUIDField(
        max_length=20,
        unique=True,
        primary_key=True,
        default=uuid.uuid4,
        db_index=True
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes", null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes", null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["like_id"], name="like_id_idx"),
            models.Index(fields=["post"], name="post_like_idx"),
            models.Index(fields=['comment'], name='comment-idx')
        ]
    
    def __str__(self):
        return f"Likes({self.user.full_name}, {self.post.pk})"


    def soft_delete(self):
        if not hasattr(self, "is_active"):
            raise ValueError("is_active field is required")

        self.is_active = False
        self.save(update_fields=("is_active",))
        return  None


class Repost(models.Model):
    """
    Represents a user reposting (sharing/vouching for) another user's post.
    This model tracks reposts separately from the parent-child relationship in Post
    to enable better ranking signals — reposts with meaningful comments from trusted
    users are strong vouching signals in the recommendation algorithm.
    """
    repost_id = models.UUIDField(
        max_length=20,
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
        db_index=True
    )
    
    # The original post being reposted
    original_post = models.ForeignKey(
        Post,
        on_delete=models.DO_NOTHING,
        related_name='repost_records'
    )
    
    # The user who is reposting
    reposted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_reposts'
    )
    
    # Optional meaningful comment that acts as a vouching signal
    # When non-empty, indicates the reposter is actively endorsing the post
    comment = models.TextField(blank=True, null=True)
    
    # Timestamp when the repost occurred
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['original_post'], name='repost_original_post_idx'),
            models.Index(fields=['reposted_by'], name='repost_user_idx'),
            models.Index(fields=['created_at'], name='repost_created_idx')
        ]
        # Prevent duplicate reposts from the same user
        constraints = [
            models.UniqueConstraint(
                fields=['original_post', 'reposted_by'],
                name='unique_user_post_repost'
            )
        ]
    
    def __str__(self):
        return f"Repost({self.reposted_by.full_name}, {self.original_post.post_id})"


class UserPostInteraction(models.Model):
    """
    Tracks user interactions with posts to inform recommendation relevance scoring
    and to exclude already-seen posts from the feed.
    
    Interaction types:
    - 'view': User has seen the post
    - 'like': User has liked the post
    - 'comment': User has commented on the post
    - 'repost': User has reposted the post
    """
    class InteractionType(models.TextChoices):
        VIEW = 'view', 'View'
        LIKE = 'like', 'Like'
        COMMENT = 'comment', 'Comment'
        REPOST = 'repost', 'Repost'
    
    interaction_id = models.UUIDField(
        max_length=20,
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
        db_index=True
    )
    
    # The user who interacted
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='post_interactions'
    )
    
    # The post being interacted with
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='user_interactions'
    )
    
    # Type of interaction (view, like, comment, repost)
    interaction_type = models.CharField(
        max_length=20,
        choices=InteractionType.choices,
        default=InteractionType.VIEW
    )
    
    # Timestamp when the interaction occurred
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='interaction_user_idx'),
            models.Index(fields=['post'], name='interaction_post_idx'),
            models.Index(fields=['user', 'post'], name='interaction_user_post_idx'),
            models.Index(fields=['interaction_type'], name='interaction_type_idx'),
            models.Index(fields=['created_at'], name='interaction_created_idx')
        ]
        # Track unique view per post per user
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post', 'interaction_type'],
                name='unique_user_post_interaction'
            )
        ]
    
    def __str__(self):
        return f"Interaction({self.user.full_name}, {self.post.post_id}, {self.interaction_type})"
