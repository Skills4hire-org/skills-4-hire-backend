import logging

from django.db.models import Count

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .core.paginations import  ReviewPagination
from .core.permissions import (
    CanModifyReviewOrReadOnly, CanRateOrReview
)
from .models import ProfileReview
from .serializers import (
    ReviewUpdateSerializer,
    ReviewCreateSerializer, ReviewDetailSerializer, 
)
logger = logging.getLogger(__name__)

class ReviewViewSet(viewsets.ModelViewSet):
    pagination_class = ReviewPagination
    http_method_names = ['post', 'get', 'patch']

    def get_permissions(self):
        if self.action == "create":
            return [CanRateOrReview()]
        return [CanModifyReviewOrReadOnly()]

    def get_serializer_class(self):
        if self.action == "create":
            return ReviewCreateSerializer
        elif self.action == "partial_update":
            return ReviewUpdateSerializer
        elif self.action == 'retrieve':
            return ReviewDetailSerializer
        return ReviewDetailSerializer

    def get_output_serializer_create(self, serializer):
        return ReviewDetailSerializer(serializer)

    def get_queryset(self):
        """" A queryset that filters by passing user 'profile' as query_params 
            or by the current provider
        """
        user = self.request.user
        queryset = ProfileReview.objects\
            .select_related("reviewed_by", "provider_profile")\
            .prefetch_related("provider_profile__profile")\
            .filter(is_active=True)
        
        if self.request.user.is_customer:
            queryset = queryset.filter(
                reviewed_by=user
            )
        else:
            queryset = queryset.filter(provider_profile__profile__user=user)
        
        return queryset
        
        