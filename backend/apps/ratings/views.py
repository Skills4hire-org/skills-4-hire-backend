import logging
from sys import is_stack_trampoline_active

from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.inspectors.field import serializer_field_to_basic_type

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from uritemplate import partial

from .core.paginations import ReviewRatingPagination
from .core.permissions import IsCreatorOrReadOnly
from .models import ProfileReview, ProfileRating
from .serializers import ReviewSerializer, RatingSerializer, RatingCreateSerializer, RatingDetailSerializer, \
    ReviewCreateSerializer, ReviewDetailSerializer
from ..core.utils.py import log_action, get_or_none

logger = logging.getLogger(__name__)


class RatingViewSet(viewsets.ModelViewSet):

    action = 'rating'
    view =  ProfileRating

    pagination_class = ReviewRatingPagination
    permission_classes =  [IsCreatorOrReadOnly]
    http_method_names = ['post', 'patch', 'get', 'delete']

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return RatingCreateSerializer
        elif self.action == "retrieve":
            return RatingDetailSerializer
        return RatingSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = ProfileRating.objects.select_related(
            "rate_by", "customer_profile", "provider_profile"
        ).filter(
            Q(customer_profile__profile__user=user)|
            Q(provider_profile__profile__user=user)
        ).order_by("-created_at").prefetch_related(
            "customer_profile__profile", "provider_profile__profile")


        if not queryset:
            return ProfileRating.objects.none()
        return queryset

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

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_object(self):
        obj_pk = self.kwargs.get("pk", "")
        if obj_pk is None:
            raise NotFound("pk not found")
        obj = get_or_none(self.view, pk=obj_pk, is_active=True)
        if obj is None:
            raise NotFound(f"{self.view} instance not found")
        self.check_object_permissions(self.request, obj)
        return obj

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_able_modify(request.user):
            raise PermissionDenied()

        serializer = self.get_serializer(
            instance, data=request.data,
            partial=True, context={"request": request})

        serializer.is_valid(raise_exception=True)

        saved_instance = serializer.save()
        return Response(data=self.get_output_serializer_create(saved_instance).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_able_modify(request.user):
            raise PermissionDenied()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewViewSet(RatingViewSet):
    action = "review"
    view = ProfileReview

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return ReviewCreateSerializer
        elif self.action == 'retrieve':
            return ReviewDetailSerializer
        return ReviewSerializer

    def get_output_serializer_create(self, serializer):
        return ReviewSerializer(serializer)

    def get_queryset(self):
        user = self.request.user
        queryset = ProfileReview.objects.select_related(
            "reviewed_by", "customer_profile", "provider_profile"
        ).filter(
            Q(customer_profile__profile__user=user) |
            Q(provider_profile__profile__user=user)
        ).order_by("-created_at").prefetch_related(
            "customer_profile__profile", "provider_profile__profile")

        if not queryset:
            return ProfileReview.objects.none()
        return queryset