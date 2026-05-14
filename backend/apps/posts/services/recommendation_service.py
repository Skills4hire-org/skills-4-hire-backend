"""
Post Recommendation Service

This module implements a multi-signal scoring algorithm to recommend posts to users.
It generates ranked feeds of posts that are likely to be of interest based on:
- Creator's trust score (reputation from completed jobs, ratings, endorsements)
- Post engagement (likes, comments, reposts)
- Relevance (location, category, past behavior)
- Recency (newer posts get a slight edge)
- Social vouching (trusted users endorsing the post)

The service follows a three-layer architecture:
1. Candidate Generation: Filter to publishable posts the user hasn't seen
2. Scoring: Multi-signal scoring algorithm
3. Ranking: Sort by score and apply active user boost
"""

import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import QuerySet, Max
from django.contrib.auth import get_user_model

from ..models import Post, UserPostInteraction

User = get_user_model()
logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Stateless service for generating ranked post feeds.
    Implements a multi-signal scoring algorithm with clear separation of concerns.
    
    Usage:
        service = RecommendationService(user=request.user)
        feed = service.get_feed(category=None, location=None, exclude_seen=True)
    """
    
    # Configuration constants
    DEFAULT_DAYS_LOOKBACK = 30  # Posts created within last 30 days
    REPOST_TRUST_THRESHOLD = 0.6  # Min trust score for reposter to boost signal
    ACTIVE_USER_BOOST = 1.1  # Multiply score by this for active user posts
    
    # Scoring weights (must sum to 1.0)
    WEIGHT_TRUST = 0.35
    WEIGHT_ENGAGEMENT = 0.25
    WEIGHT_RELEVANCE = 0.20
    WEIGHT_RECENCY = 0.10
    WEIGHT_REPOST = 0.10
    
    def __init__(self, user: User):
        """
        Initialize the recommendation service for a specific user.
        
        Args:
            user: User object for whom to generate recommendations
        """
        self.user = user
        self.user_profile = getattr(user, 'profile', None)
        
    def get_feed(
        self,
        category: str = None,
        location: str = None,
        exclude_seen: bool = True,
        limit: int = 20,
        offset: int = 0
    ) -> list:
        """
        Generate a ranked feed of recommended posts for the user.
        
        Args:
            category: Optional category slug to filter candidates
            location: Optional location override for relevance matching
            exclude_seen: Whether to exclude posts user has already viewed
            limit: Number of results to return (max 50)
            offset: Number of results to skip for pagination
            
        Returns:
            List of dicts with post data and recommendation_score
        """
        # Layer 1: Candidate Generation
        candidates = self._get_candidates(
            category=category,
            exclude_seen=exclude_seen
        )
        
        if not candidates:
            return []
        
        # Layer 2: Scoring
        scored_posts = []
        max_engagement = self._get_max_engagement(candidates)
        
        for post in candidates:
            score = self._score_post(
                post=post,
                max_engagement=max_engagement,
                user_location=location or (self.user_profile.location if self.user_profile else None)
            )
            scored_posts.append({
                'post': post,
                'score': score
            })
        
        # Layer 3: Ranking + Active User Boost
        ranked_posts = self._rank_and_boost(scored_posts)
        
        # Apply pagination
        paginated = ranked_posts[offset:offset + limit]
        
        return paginated
    

    def _get_candidates(self, category: str = None, exclude_seen: bool = True) -> QuerySet:
        """
        Generate candidates: published posts created in last N days that the user
        hasn't seen and didn't create themselves.
        
        Args:
            category: Optional category slug to filter
            exclude_seen: Whether to exclude already-viewed posts
            
        Returns:
            Optimized QuerySet of candidate posts
        """
        # Start with published posts that are not deleted
        candidates = Post.objects.filter(
            is_published=True,
            is_active=True,
            is_deleted=False
        )
        
        # Filter by creation time (last 30 days)
        cutoff_date = timezone.now() - timedelta(days=self.DEFAULT_DAYS_LOOKBACK)
        candidates = candidates.filter(created_at__gte=cutoff_date)
        
        # Exclude posts created by the current user
        candidates = candidates.exclude(user=self.user)
        
        # Exclude already-seen posts if requested
        if exclude_seen:
            seen_post_ids = UserPostInteraction.objects.filter(
                user=self.user,
                interaction_type=UserPostInteraction.InteractionType.VIEW
            ).values_list('post_id', flat=True)
            candidates = candidates.exclude(post_id__in=seen_post_ids)
        
        # Filter by category if provided
        if category:
            candidates = candidates.filter(tags__name__icontains=category)
        
        # Optimize query with select_related and prefetch_related
        candidates = candidates.select_related(
            'user',
            'user__profile'
        ).prefetch_related(
            'tags',
            'likes',
            'comments',
            'repost_records'
        ).distinct()
        
        return candidates
    
    def _score_post(
        self,
        post: Post,
        max_engagement: int,
        user_location: str = None
    ) -> float:
        """
        Compute the recommendation score for a post using the multi-signal algorithm.
        
        Score = (trust × 0.35) + (engagement × 0.25) + (relevance × 0.20) +
                (recency × 0.10) + (repost_boost × 0.10)
        
        Args:
            post: Post object to score
            max_engagement: Maximum engagement count in candidate pool
            user_location: User's location for relevance matching
            
        Returns:
            Float score between 0.0 and 1.0+
        """
        trust = self._trust_score(post)
        engagement = self._engagement_score(post, max_engagement)
        relevance = self._relevance_score(post, user_location)
        recency = self._recency_score(post)
        repost_boost = self._repost_boost(post)
        
        score = (
            trust * self.WEIGHT_TRUST +
            engagement * self.WEIGHT_ENGAGEMENT +
            relevance * self.WEIGHT_RELEVANCE +
            recency * self.WEIGHT_RECENCY +
            repost_boost * self.WEIGHT_REPOST
        )
        
        return score
    
    def _trust_score(self, post: Post) -> float:
        """
        Returns the post creator's normalized trust_score (0.0–1.0).
        
        Trust score is the single most important signal. It reflects provider reputation
        via completed jobs, ratings, and endorsements. Users are more likely to engage
        with posts from trustworthy creators.
        
        Args:
            post: Post object whose creator's trust is being scored
            
        Returns:
            Float between 0.0 and 1.0
        """
        if not post.user or not hasattr(post.user, 'profile'):
            return 0.0
        
        trust = getattr(post.user.profile, 'trust_score', 0.0)
        # Ensure it's normalized to [0.0, 1.0]
        return min(max(float(trust), 0.0), 1.0)
    
    def _engagement_score(self, post: Post, max_engagement: int) -> float:
        """
        Normalize engagement_count relative to the max in the candidate pool.
        
        Measures how much the community has reacted — likes, comments, reposts
        all contribute. Higher engagement indicates community validation.
        
        Args:
            post: Post object to score
            max_engagement: Maximum engagement count in the candidate pool
            
        Returns:
            Float between 0.0 and 1.0
        """
        if max_engagement == 0:
            return 0.0
        
        engagement = getattr(post, 'engagement_count', 0)
        normalized = min(float(engagement) / max_engagement, 1.0)
        return normalized
    
    def _relevance_score(self, post: Post, user_location: str = None) -> float:
        """
        Compute relevance based on location, category, and past behavior.
        
        Relevance combines location, category match, and past behavior. Posts that
        align with user's interests and previous engagement patterns score higher.
        
        Scoring breakdown:
        - +0.5 if post location matches user location
        - +0.5 if post category matches user's category interests
        - Consider past behavior if available
        
        Args:
            post: Post object to score
            user_location: User's location for matching
            
        Returns:
            Float between 0.0 and 1.0
        """
        relevance_score = 0.0
        
        # Location matching
        post_location = post.city or ""
        if user_location and post_location.lower() == user_location.lower():
            relevance_score += 0.5
        
        # Category matching
        if self.user_profile:
            post_categories = set(tag.name.lower() for tag in post.tags.all())
            user_interests = getattr(self.user_profile, 'category_interest', [])
            
            if isinstance(user_interests, list):
                user_interests_lower = {cat.lower() for cat in user_interests}
                if post_categories & user_interests_lower:
                    relevance_score += 0.5
        
        # Past behavior: check if user has interacted with this category before
        # (This could be expanded to a more sophisticated behavior model)
        if post.tags.exists():
            past_interactions = UserPostInteraction.objects.filter(
                user=self.user,
                post__tags__in=post.tags.all()
            ).count()
            if past_interactions > 0:
                relevance_score = min(relevance_score + 0.2, 1.0)
        
        return min(relevance_score, 1.0)
    
    def _recency_score(self, post: Post) -> float:
        """
        Score posts based on recency using exponential decay.
        
        Newer posts get a slight edge. Formula: score = 1 / (1 + days_since_posted)
        This is the weakest signal; we don't want to over-emphasize age.
        
        Args:
            post: Post object to score
            
        Returns:
            Float between 0.0 and 1.0
        """
        now = timezone.now()
        days_since_posted = (now - post.created_at).days
        
        # Exponential decay: 1 / (1 + days)
        # At 0 days: 1.0, at 1 day: 0.5, at 7 days: 0.125, etc.
        recency = 1.0 / (1.0 + max(days_since_posted, 0))
        
        return recency
    
    def _repost_boost(self, post: Post) -> float:
        """
        Compute repost boost signal from trusted users endorsing the post.
        
        A repost from a trusted user is a strong ranking signal — it means a
        trusted person is vouching for this post, not just sharing it.
        
        Returns non-zero only if:
        1. The reposter has a trust_score above threshold (e.g. > 0.6)
        2. The repost has a non-empty comment (meaningful comment = vouching signal)
        3. The reposter shares the same location or category_interest as the viewer
        
        Args:
            post: Post object being scored
            
        Returns:
            Float boost value (0.0 if no qualified reposts, otherwise 0.0-1.0)
        """
        boost = 0.0
        
        # Get all active reposts for this post
        reposts = post.repost_records.filter(is_active=True).select_related(
            'reposted_by',
            'reposted_by__profile'
        )
        
        if not reposts.exists():
            return 0.0
        
        # Score each repost and accumulate weighted boost
        qualified_boost_count = 0
        
        for repost in reposts:
            reposter = repost.reposted_by
            reposter_profile = getattr(reposter, 'profile', None)
            
            # Check 1: Reposter trust score above threshold
            reposter_trust = getattr(reposter_profile, 'trust_score', 0.0) if reposter_profile else 0.0
            if reposter_trust < self.REPOST_TRUST_THRESHOLD:
                continue
            
            # Check 2: Repost has meaningful comment
            if not repost.comment or repost.comment.strip() == "":
                continue
            
            # Check 3: Reposter shares location or category interest with viewer
            shares_location = False
            shares_category = False
            
            if reposter_profile and self.user_profile:
                reposter_location = getattr(reposter_profile, 'location', '')
                if reposter_location and self.user_profile.location:
                    shares_location = reposter_location.lower() == self.user_profile.location.lower()
                
                reposter_interests = getattr(reposter_profile, 'category_interest', [])
                user_interests = getattr(self.user_profile, 'category_interest', [])
                if isinstance(reposter_interests, list) and isinstance(user_interests, list):
                    shares_category = bool(set(reposter_interests) & set(user_interests))
            
            # If qualified, increment count
            if shares_location or shares_category:
                qualified_boost_count += 1
        
        # Convert qualified count to boost (max out at 0.5 to prevent over-boosting)
        if qualified_boost_count > 0:
            boost = min(qualified_boost_count * 0.2, 0.5)
        
        return boost
    
    
    def _rank_and_boost(self, scored_posts: list) -> list:
        """
        Sort posts by score and apply active user boost.
        
        Posts from users flagged as is_active_user=True get a 1.1x boost to
        promote content from engaged community members.
        
        Args:
            scored_posts: List of dicts with 'post' and 'score' keys
            
        Returns:
            List of dicts sorted by final score (descending)
        """
        # Apply active user boost
        for item in scored_posts:
            post = item['post']
            if post.user and hasattr(post.user, 'profile'):
                is_active = getattr(post.user.profile, 'is_active_user', False)
                if is_active:
                    item['score'] *= self.ACTIVE_USER_BOOST
        
        # Sort by score descending
        ranked = sorted(scored_posts, key=lambda x: x['score'], reverse=True)
        
        return ranked
    
    # ========== UTILITY METHODS ==========
    
    def _get_max_engagement(self, candidates: QuerySet) -> int:
        """
        Get the maximum engagement_count in the candidate pool for normalization.
        
        Args:
            candidates: QuerySet of candidate posts
            
        Returns:
            Integer max engagement count
        """
        # Use engagement_count field
        max_engagement = candidates.aggregate(
            max_engagement=Max('engagement_count')
        ).get('max_engagement', 0) or 0
        
        return max_engagement
