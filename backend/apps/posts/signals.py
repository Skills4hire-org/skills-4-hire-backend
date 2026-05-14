
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from pyexpat.errors import messages
from django.utils import timezone

from .models import Likes, Comment, UserPostInteraction, Repost, Post
from apps.notification.events import NotificationEvents
from .services.trust_score_service import compute_trust_score
from ..bookings.models import Bookings

from asyncio.log import  logger

# ========== ENGAGEMENT AND RECOMMENDATION SIGNALS ==========

@receiver(post_save, sender=UserPostInteraction)
def update_engagement_on_interaction(sender, created, instance, **kwargs):
    """
    Update post engagement_count whenever a UserPostInteraction is created or updated.
    
    This keeps the engagement_count field synchronized with actual likes, comments, and reposts.
    The engagement_count is used in the recommendation ranking algorithm.
    """
    if not instance.post:
        return
    
    try:
        post = instance.post
        likes_count = post.likes.filter(is_active=True).count()
        comments_count = post.comments.filter(is_active=True).count()
        reposts_count = post.repost_records.filter(is_active=True).count()
        
        engagement = likes_count + comments_count + reposts_count
        
        if post.engagement_count != engagement:
            post.engagement_count = engagement
            post.save(update_fields=['engagement_count'])
            
    except Exception as e:
        logger.error(f"Error updating engagement count on interaction: {e}")


@receiver(post_delete, sender=UserPostInteraction)
def update_engagement_on_interaction_delete(sender, instance, **kwargs):
    """
    Update post engagement_count when a UserPostInteraction is deleted.
    """
    if not instance.post:
        return
    
    try:
        post = instance.post
        likes_count = post.likes.filter(is_active=True).count()
        comments_count = post.comments.filter(is_active=True).count()
        reposts_count = post.repost_records.filter(is_active=True).count()
        
        engagement = likes_count + comments_count + reposts_count
        post.engagement_count = engagement
        post.save(update_fields=['engagement_count'])
        
    except Exception as e:
        logger.error(f"Error updating engagement count on interaction delete: {e}")


@receiver(post_save, sender=Repost)
def update_engagement_on_repost(sender, created, instance, **kwargs):
    """
    Update post engagement_count when a Repost is created.
    
    This signal is called in addition to UserPostInteraction to ensure
    the engagement count is always accurate.
    """
    if not created or not instance.original_post:
        return
    
    try:
        post = instance.original_post
        likes_count = post.likes.filter(is_active=True).count()
        comments_count = post.comments.filter(is_active=True).count()
        reposts_count = post.repost_records.filter(is_active=True).count()
        
        engagement = likes_count + comments_count + reposts_count
        post.engagement_count = engagement
        post.save(update_fields=['engagement_count'])
        
    except Exception as e:
        logger.error(f"Error updating engagement count on repost: {e}")


@receiver(post_save, sender=Likes)
def update_engagement_on_like(sender, created, instance, **kwargs):
    """
    Update post engagement_count when a Like is created.
    
    This keeps the engagement_count synchronized when likes are created
    through the existing Like model.
    """
    if not created or not instance.post:
        return
    
    try:
        post = instance.post
        likes_count = post.likes.filter(is_active=True).count()
        comments_count = post.comments.filter(is_active=True).count()
        reposts_count = post.repost_records.filter(is_active=True).count()
        
        engagement = likes_count + comments_count + reposts_count
        post.engagement_count = engagement
        post.save(update_fields=['engagement_count'])
        
    except Exception as e:
        logger.error(f"Error updating engagement count on like: {e}")


@receiver(post_save, sender=Comment)
def update_engagement_on_comment(sender, created, instance, **kwargs):
    """
    Update post engagement_count when a Comment is created.
    
    This keeps the engagement_count synchronized when comments are created.
    """
    if not created or not instance.post:
        return
    
    try:
        post = instance.post
        likes_count = post.likes.filter(is_active=True).count()
        comments_count = post.comments.filter(is_active=True).count()
        reposts_count = post.repost_records.filter(is_active=True).count()
        
        engagement = likes_count + comments_count + reposts_count
        post.engagement_count = engagement
        post.save(update_fields=['engagement_count'])
        
    except Exception as e:
        logger.error(f"Error updating engagement count on comment: {e}")


# ========== TRUST SCORE SIGNALS ==========

@receiver(post_save, sender=Bookings)
def update_trust_score_on_booking_completion(sender, instance, created, **kwargs):
    """
    Update provider's trust score when a booking is marked as COMPLETED.
    
    This can be called via:
    1. Signals when booking status changes to COMPLETED
    2. Scheduled Celery tasks for batch updates
    
    The trust score is computed from:
    - Completed jobs/bookings
    - Average rating from reviews
    - Endorsements count
    """

    if instance.booking_status != Bookings.BookingStatus.COMPLETED:
        return
    
    try:
        # Get the provider's user
        provider_user = instance.provider.profile.user
        
        # Compute and update trust score
        trust_score = compute_trust_score(provider_user)
        
        if provider_user.profile:
            provider_user.profile.trust_score = trust_score
            provider_user.profile.save(update_fields=['trust_score'])
            logger.info(f"Updated trust score for user {provider_user.id}: {trust_score:.3f}")
            
    except Exception as e:
        logger.error(f"Error updating trust score on booking completion: {e}")

from ..chats.endorsements.models import Endorsements

@receiver(post_save, sender=Endorsements)
def update_trust_score_on_endorsement(sender, instance, created, **kwargs):

    """
    Update user trust score when an endorsement is added to the user profile
    """
    

    if not isinstance(instance, Endorsements) or not created:
        return
    
    try:
        provider_user = getattr(instance.provider.profile, "user", None)

        trust_score = compute_trust_score(provider_user)

  
        if provider_user.profile:
            provider_user.profile.trust_score = trust_score
            provider_user.profile.save(update_fields=['trust_score'])
            logger.info(f"Updated trust score for user {provider_user.id}: {trust_score:.3f}")
            
    except Exception as e:
        logger.error(f"Error updating trust score on endorsement creation: {e}")

from ..ratings.models import ProfileReview

@receiver(post_save, sender=ProfileReview)
def update_trust_score_on_review(sender, instance, created, **kwargs):
    if not isinstance(instance, ProfileReview) or not created:
        return 
    
    try:
        provider_user = getattr(instance.provider_profile.profile, "user", None)

        trust_score = compute_trust_score(provider_user)
        if provider_user.profile:
            provider_user.profile.trust_score = trust_score
            provider_user.profile.save(update_fields=['trust_score'])
            logger.info(f"Updated trust score for user {provider_user.id}: {trust_score:.3f}")
            
    except Exception as e:
        logger.error(f"Error updating trust score on rating creation: {e}")
                                
def update_user_last_active(sender, instance, created, **kwargs):
    """
    Update user's last_active timestamp on any interaction.
    
    Called when:
    - User creates a post
    - User creates a comment
    - User likes/unlikes a post
    - User reposts
    """

    if  isinstance(instance, Repost):
        user = instance.reposted_by
    else:
        user = instance.user
        
    if not user:
        return
    try:
        profile = getattr(user, "profile", None)
        if profile:
            profile.last_active = timezone.now()
            profile.save(update_fields=['last_active'])
            
    except Exception as e:
        logger.error(f"Error updating user last_active: {e}")


post_save.connect(update_user_last_active, sender=Post)
post_save.connect(update_user_last_active, sender=Repost)
post_save.connect(update_user_last_active, sender=Comment)
post_save.connect(update_user_last_active, sender=Likes)
post_save.connect(update_user_last_active, sender=UserPostInteraction)
post_delete.connect(update_user_last_active, sender=Likes)
