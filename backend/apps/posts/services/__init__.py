"""
Posts app services module.

Contains business logic for post operations including recommendations, scoring,
and engagement tracking.
"""

from .recommendation_service import RecommendationService
from .trust_score_service import compute_trust_score

__all__ = [
    'RecommendationService',
    'compute_trust_score',
]
