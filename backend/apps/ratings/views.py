import logging

from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from .models import ProfileReview, ProfileRating
from .serializers import ReviewSerializer, RatingSerializer
from ..posts.permission import IsOwnerOrReadOnly
from .utils.profiles import get_profile_by_id

logger = logging.getLogger(__name__)


class ReviewViewSet(viewsets.ModelViewSet):

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    queryset = (
        ProfileReview.objects.filter(is_active=True, is_deleted=False)
        .select_related('reviewed_by', 'profile')
    )

    def get_queryset(self):
        """If `profile_id` is present in the URL, filter reviews for that profile."""
        profile_id = self.kwargs.get('profile_id')
        qs = self.queryset.all()
        if profile_id:
            profile = get_profile_by_id(profile_id)
            if not profile.get('success'):
                raise NotFound(detail=profile.get('detail') or 'Profile not found')
            qs = qs.filter(profile=profile.get('profile'))
        return qs.order_by('-created_at')

    @method_decorator(cache_page( 60 * 15 ))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        profile_pk = self.kwargs.get('profile_id')
        if not profile_pk:
            raise ValidationError({'profile_id': 'Profile ID is required to create a review.'})

        profile = get_profile_by_id(profile_pk)
        if not profile.get('success'):
            raise NotFound(detail=profile.get('detail') or 'Profile not found')

        profile_instance = profile.get('profile')

        if getattr(request.user, 'profile', None) == profile_instance:
            raise ValidationError({'detail': 'You cannot review your own profile.'})

        serializer = self.get_serializer(data=request.data, context={'request': request, 'profile': profile_instance})
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                serializer.save(profile=profile_instance, reviewed_by=request.user)
        except Exception:
            logger.exception('Saving review object failed')
            raise

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        obj = self.get_object()
        if not isinstance(obj, ProfileReview):
            logger.error("provided object is not a ProfileReview instance")
            raise ValidationError("object is not a review instance")
        if not obj.can_edit(self.request.user):
            logger.warning('Unauthorized edit attempt for review %s by %s', obj.review_id, self.request.user)
            raise PermissionDenied('You do not have permission to edit this review.')
        serializer.save()

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not isinstance(instance, ProfileReview):
            logger.error("provided object is not a ProfileReview instance")
            raise ValidationError("object is not a review instance")
        if not instance.can_edit(request.user):
            logger.warning('Unauthorized delete attempt for review %s by %s', instance.review_id, request.user)
            raise PermissionDenied('You do not have permission to delete this review.')
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

        

class RatingViewSet(ReviewViewSet):
    serializer_class = RatingSerializer

    queryset = (
        ProfileRating.objects.filter(
            is_active=True, is_deleted=False
        ).select_related("rate_by", "profile")
    )

    def perform_update(self, serializer):
        obj = self.get_object()
        if not isinstance(obj, ProfileRating):
            logger.error("provided object is not a ProfileRating instance")
            raise ValidationError("object is not a rating instance")
        if not obj.can_edit(self.request.user):
            logger.warning('Unauthorized edit attempt for rating %s by %s', obj.review_id, self.request.user)
            raise PermissionDenied('You do not have permission to edit this rating.')
        serializer.save()

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not isinstance(instance, ProfileRating):
            logger.error("provided object is not a ProfileRating instance")
            raise ValidationError("object is not a rating instance")
        if not instance.can_edit(request.user):
            logger.warning('Unauthorized delete attempt for rating %s by %s', instance.review_id, request.user)
            raise PermissionDenied('You do not have permission to delete this review.')
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)