"""
Trust Score Service

Computes and updates a user's trust_score based on:
- Completed jobs/bookings
- Average rating from reviews
- Endorsements count

The trust score is the most important ranking signal for post recommendations,
as it reflects provider reputation and reliability.

Can be called via:
1. Django signals (on booking completion, rating creation, endorsement)
2. Scheduled Celery tasks (for periodic updates)
"""

import logging
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count

logger = logging.getLogger(__name__)

User = get_user_model()


def compute_trust_score(user: User) -> float:
    """
    Compute and return a user's trust score.
    
    Trust score components:
    - completed_jobs_count: Each completed job = +0.05 (capped at 0.50)
    - average_rating: Normalized from 5-star scale to 0.0–0.30
    - endorsements_count: Each endorsement = +0.02 (capped at 0.20)
    
    The final score is normalized to the range [0.0, 1.0].
    
    Usage:
        # Via signals (on booking completion or rating creation):
        trust_score = compute_trust_score(user)
        user.profile.trust_score = trust_score
        user.profile.save()
        
        # Via Celery task (for batch updates):
        for user in User.objects.filter(is_provider=True):
            compute_trust_score(user)
    
    Args:
        user: User object for whom to compute trust score
        
    Returns:
        Float between 0.0 and 1.0 representing the user's trust score
    """
    trust_score = 0.0
    
    try:
        # Get or create user profile
        profile = getattr(user, 'profile', None)
        if not profile:
            logger.warning(f"User {user.id} has no profile; returning 0.0")
            return 0.0
        
        # Component 1: Completed jobs count
        # Each completed job contributes +0.05, max contribution 0.50
        completed_jobs = _get_completed_jobs_count(user)
        jobs_contribution = min(completed_jobs * 0.05, 0.50)
        
        # Component 2: Average rating from reviews
        # Ratings are on 5-star scale; normalize to 0.30 max contribution
        avg_rating = _get_average_rating(user)
        if avg_rating:
            # Normalize 5-star to 0-1, then scale to 0.30 contribution
            normalized_rating = (avg_rating - 1.0) / 4.0  # Maps [1, 5] to [0, 1]
            rating_contribution = normalized_rating * 0.30
        else:
            rating_contribution = 0.0
        
        # Component 3: Endorsements count
        # Each endorsement contributes +0.02, max contribution 0.20
        endorsements_count = _get_endorsements_count(user)
        endorsements_contribution = min(endorsements_count * 0.02, 0.20)
        
        # Sum all components
        trust_score = jobs_contribution + rating_contribution + endorsements_contribution
        
        # Cap at 1.0
        trust_score = min(trust_score, 1.0)
        
        logger.info(
            f"Computed trust score for user {user.id}: {trust_score:.3f} "
            f"(jobs={jobs_contribution:.2f}, rating={rating_contribution:.2f}, "
            f"endorsements={endorsements_contribution:.2f})"
        )
        
    except Exception as e:
        logger.error(f"Error computing trust score for user {user.id}: {e}")
        trust_score = 0.0
    
    return trust_score

def _get_completed_jobs_count(user: User) -> int:
    """
    Get the count of completed bookings/jobs for the user.
    
    Checks for bookings with status "COMPLETED" where the user is the provider or the customer.
    
    Args:
        user: User object
        
    Returns:
        Integer count of completed jobs
    """
    try:
        # Import here to avoid circular imports
        from apps.bookings.models import Bookings
        
        # Check if user is a provider and has completed bookings
        if not getattr(user, 'is_provider', False):
            return 0
        
        completed_count = Bookings.objects.filter(
            booking_status=Bookings.BookingStatus.COMPLETED
        )
        if user.is_provider:
            completed_count = completed_count.filter(provider__profile__user=user).count()
        else:
            completed_count = completed_count.filter(customer=user).count()
        
        return completed_count
    except Exception as e:
        logger.warning(f"Error getting completed jobs for user {user.id}: {e}")
        return 0


def _get_average_rating(user: User) -> float:
    """
    Get the average rating for a user from their profile reviews.
    
    Reviews are aggregated from the ratings app.
    
    Args:
        user: User object
        
    Returns:
        Float average rating (1-5 scale) or None if no ratings exist
    """
    try:
        # Import here to avoid circular imports
        from apps.ratings.models import ProfileReview
        
        # Get average rating for this user's provider profile
        provider_profile = getattr(user.profile, 'provider_profile', None)
        if not provider_profile:
            return None
        
        avg_rating = ProfileReview.objects.filter(
            provider_profile=provider_profile,
            is_active=True
        ).aggregate(avg_rating=Avg('ratings')).get('avg_rating')
        
        return avg_rating
    except Exception as e:
        logger.warning(f"Error getting average rating for user {user.id}: {e}")
        return None

def _get_endorsements_count(user: User) -> int:
    """
    Get the count of endorsements for a user.
    
    This is a placeholder that can be implemented when an endorsement model exists.
    Currently returns 0.
    
    Args:
        user: User object
        
    Returns:
        Integer count of endorsements
    """
    try:
        from ...chats.endorsements.models import Endorsements

        provider = getattr(user.profile, "provider_profile", None)

        endorsements_count = Endorsements.objects.filter(
            provider=provider,
            is_active=True
        ).count()
        
        return endorsements_count
    except Exception as e:
        logger.warning(f"Error getting endorsements for user {user.id}: {e}")
        return 0
