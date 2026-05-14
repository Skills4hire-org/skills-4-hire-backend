"""
Feed serializer for the recommendation feed endpoint.

Includes all core post fields, creator information with trust score,
engagement metrics, and recommendation score from the ranking algorithm.
"""

from rest_framework import serializers
from ..models import Post
from .read import JobPostSerializer



class FeedPostSerializer(JobPostSerializer):
    """
    Serializer for posts in the personalized feed/recommendation endpoint.
    
    Includes:
    - All core post fields (title, content, type, timestamps)
    - Creator profile with trust_score and location
    - Engagement metrics (likes, comments, reposts)
    - Repost information (is_reposted, repost_comment if applicable)
    - Recommendation score (passed via context from the view)
    
    The recommendation_score is injected by the view based on the ranking
    algorithm's multi-signal scoring.
    """
    
    # Recommendation score from the ranking algorithm
    # Passed via context: serializer = FeedPostSerializer(post, context={'recommendation_score': 0.85})
    recommendation_score = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = JobPostSerializer.Meta.model
        fields = JobPostSerializer.Meta.fields + [
            "recommendation_score"
        ]
     
    def get_recommendation_score(self, obj) -> float:
        """
        Retrieve the recommendation score from context.
        
        The view is responsible for computing the score using
        RecommendationService and passing it via context.
        
        Args:
            obj: Post instance
            
        Returns:
            Float between 0.0 and ~1.5 (may exceed 1.0 due to active user boost)
        """
        # Get the recommendation_score from the view context
        context = self.context or {}
        return context.get('recommendation_score', 0.0)
