import logging

from django.db.models import Count

from rest_framework import viewsets, status
from rest_framework.response import Response

from .core.paginations import RatingPagination, ReviewPagination
from .core.permissions import (
    CanModifyReviewOrReadOnly, CanRateOrReview, CanModifyRatingOrReadOnly
)
from .models import ProfileReview, ProfileRating
from .serializers import (
    ReviewSerializer, RatingSerializer, RatingCreateSerializer, 
    RatingDetailSerializer, ReviewUpdateSerializer,
    ReviewCreateSerializer, ReviewDetailSerializer, 
    RatingUpdateSerializer
)
from ..core.utils.py import log_action

logger = logging.getLogger(__name__)


class RatingViewSet(viewsets.ModelViewSet):
    action = 'rating'
    view =  ProfileRating

    pagination_class = RatingPagination
    http_method_names = ['post', 'patch', 'get', 'delete']

    def get_permissions(self):
        if self.action == "create":
            return [CanRateOrReview()]
        return [CanModifyRatingOrReadOnly()]

    def get_serializer_class(self):
        if self.action in ("create"):
            return RatingCreateSerializer
        elif self.action == "partial_update":
            return RatingUpdateSerializer
        elif self.action == "retrieve":
            return RatingDetailSerializer
        return RatingSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = ProfileRating.objects\
            .select_related("rate_by", "provider_profile")\
            .prefetch_related("provider_profile__profile")\
            .annotate(total_ratings=Count("rating_id", distinct=True))\
            .filter(is_active=True)
            
        if "profile" in self.request.query_params:
            provider_id = self.request.query_params.get("profile")

            queryset.filter(provider_profile__pk=provider_id)
            return queryset
        else:
            try:
                current_user_rating = queryset.filter(provider_profile=user.profile.provider_profile)
                return current_user_rating
            except Exception:
                return ProfileRating.objects.none()


    def get_output_serializer_create(self, serializer):
        return RatingSerializer(serializer)

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        saved_serializer = serializer.save()
        log_action(
            action_type=self.action,
            user=request.user,
            details={'rating_pk': saved_serializer.pk}
        )

        output_serializer = self.get_output_serializer_create(saved_serializer)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    # @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data,
            partial=True, context={"request": request})

        serializer.is_valid(raise_exception=True)

        saved_instance = serializer.save()
        return Response(data=self.get_output_serializer_create(saved_instance).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewViewSet(RatingViewSet):
    action = "review"
    view = ProfileReview
    pagination_class = ReviewPagination

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
        return ReviewSerializer

    def get_output_serializer_create(self, serializer):
        return ReviewSerializer(serializer)

    def get_queryset(self):
        """" A queryset that filters by passing user 'profile' as query_params 
            or by the current provider
        """
        user = self.request.user
        queryset = ProfileReview.objects\
            .select_related("reviewed_by", "provider_profile")\
            .prefetch_related("provider_profile__profile")\
            .annotate(total_reviews=Count("review_id", distinct=True))\
            .filter(is_active=True)

        if "profile" in self.request.query_params:
            provider_pk = self.request.query_params.get("profile")
            queryset.filter(provider_profile__pk=provider_pk)
            return queryset
        
        else:
            try:
                current_user_reviews = queryset.filter(provider_profile__profile__user=user)
                return current_user_reviews
            except Exception:
                return ProfileReview.objects.none()
        
        