import logging
from typing import Any

from celery.worker.consumer.mingle import exception
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Model

from rest_framework import viewsets, status, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied

from .models import Post, Comment, PostLike
from .serializers import PostCreateSerializer, PostDetailSerializer, CommentSerializer
from .paginations import CustomPostPagination
from .permission import IsOwnerOrReadOnly
from .utils.posts import get_post_by_id
from .services import  return_paginated_view, LikeService, CommentService
from apps.bookings.permissions import  IsCustomer
from apps.notification.services import send_general_notification
from apps.notification.events import NotificationEvents

User = get_user_model()
logger = logging.getLogger(__name__)


class PostViewSet(viewsets.ModelViewSet):
    """
    Features:
    - explicit queryset and optimized prefetch/select
    - safe create/update/delete flows with transactions
    - `mine` action to get authenticated user's posts
    - filtering, searching and ordering support
    - caching on list endpoints
    """

    queryset = (
        Post.is_active_objects.all().filter(is_deleted=False)
        .select_related('user')
        .prefetch_related(Prefetch(lookup="likes", queryset=PostLike.is_active_objects.all()),
            Prefetch(lookup="comments", queryset=Comment.active_objects.all().order_by("-created_at")),
            'attachment', 'post_tag__service')
    )
    pagination_class = CustomPostPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['post_type', 'user', "post_tag__service_name__name"]
    search_fields = ['post_content', "post_tag"]
    ordering_fields = ['created_at', 'updated_at']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PostCreateSerializer
        return PostDetailSerializer

    def get_permissions(self):
        if self.action == "offers":
            return [IsCustomer()]
        elif self.action in ("like_post", "unlike_post"):
            return [permissions.IsAuthenticated()]
        return [IsOwnerOrReadOnly()]

    def get_queryset(self):
        # Ensure we always start from the base queryset to allow further
        # filtering by DRF filter backends.
        queryset = self.filter_queryset(self.queryset)
        return  queryset.order_by("-created_at")

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        """List posts (cached for a short period)."""
        return super().list(request, *args, **kwargs)

    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        """Create post as the authenticated user in a DB transaction."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except Exception as e:
            sts: str = "Failed"
            msg = str(e)
            code = status.HTTP_400_BAD_REQUEST
        else:
            sts: str = "success"
            msg="Post created"
            code = status.HTTP_201_CREATED
        return  Response(
            data={"status": sts, "msg": msg, "detail": serializer.data}, status=code
        )

    def perform_create(self, serializer):
        serializer.save()

    @method_decorator(transaction.atomic)
    def update(self, request, *args, **kwargs):
        """Wrap updates in a transaction and prefer partial updates where appropriate."""
        return super().update(request, *args, **kwargs)

    @method_decorator(transaction.atomic)
    def destroy(self, request, *args, **kwargs):
        return  super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance: Post):
        # Use soft delete to preserve data and indexes
        instance.soft_delete()

    @method_decorator(cache_page(60 * 10))
    @action(detail=False, methods=["get"], url_path="offers")
    def offers(self, request, include_offers: bool = True):
        """ Returns customer jobs posts with pagination"""

        if include_offers:
           qs = self.get_queryset()\
                .filter(user=request.user, post_type=Post.PostType.JOB.value)\
                .order_by("-created_at")
        else:
            qs = self.get_queryset()\
                .filter(user=request.user)\
                .order_by("-created_at")

        if qs is None:
            return  0
        return  return_paginated_view(self, qs)

    @method_decorator(cache_page(60 * 15))
    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request, *args, **kwargs):
        """Return the authenticated user's posts with normal pagination and filtering."""
        print("userType", request.user)
        return  self.offers(request, include_offers=False, **kwargs)


    @action(methods=["post"], detail=True, url_path="like")
    def like_post(self, request, *args, **kwargs):
        """
        Like a post.
        post_pk is expected in the URL kwargs.
        """
        post = self.get_object()
        user = request.user
        try:
            like_post = LikeService(post=post, user=user)
            new_like = like_post.create_like_post()
        except Exception as exc:
            logger.error(f"Failed to create a like for post {post.pk}: {exc}")
            sts = False
            msg = str(exc)
            code=400
        else:
            sts = "success"
            msg = str(new_like)
            code=201

        return Response({"status": sts, "detail": msg}, status=code)

    @action(methods=["delete"], detail=True, url_path="unlike")
    def unlike_post(self, request, *args, **kwargs):
        """
        Unlike a post.
        post_pk is expected in the URL kwargs.
        """
        post = self.get_object()
        try:
            like_post = LikeService(post=post, user=request.user)
            new_like = like_post.unlike_post()
        except Exception as exc:
            logger.error(f"Failed to unlike post {post.pk}: {exc}")
            msg= str(exc)
            sts = "failed"
            code=400
        else:
            msg="Unliked Post",
            sts="success",
            code=200
        return Response({"status": sts, "msg": msg}, status=code)

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = CustomPostPagination

    permissions = [permissions.IsAuthenticated]
    queryset = Comment.active_objects.select_related("user", "post", "parent").all()

    def get_queryset(self):
        """ return base queryset"""
        return self.queryset

    def get_object(self) -> bool | tuple[Any, Model | Any]:
        post_pk = self.kwargs.get("posts_pk")
        comment_pk = self.kwargs.get('pk')
        comment_instance = None
        if comment_pk is not None:
            comment_instance = Comment.active_objects.get(comment_id=comment_pk)
            self.check_object_permissions(self.request, comment_instance)
        else:
            comment_instance = comment_instance
        post = get_post_by_id(post_pk)
        if not post.get("success"):
            return False

        post_instance = post.get("post")

        return  post_instance, comment_instance

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        post, _ = self.get_object()
        serializer = self.get_serializer(data=request.data, context={"request": request, "post": post})
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except Exception as e:
            msg = str(e)
            code = 400
            sts = "failed"
        else:
            msg = "Comment_Added"
            code = 201
            sts = "success"
        return  Response({"status": sts, "detail": msg, }, status=code)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        _, instance = self.get_object()

        if not instance.can_edit(request.user):
            raise PermissionDenied()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return  Response(serializer.data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        _, instance  = self.get_object()
        self.perform_destroy(instance)
        return Response(status=204)

    def perform_destroy(self, instance):
        if not instance.can_edit(self.request.user):
            logger.warning(f"User {self.request.user} attempted to delete Comment {instance.pk} without permission.")
            raise PermissionDenied()
        instance.soft_delete()

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        """List comments (cached for a short period)."""
        queryset = self.filter_queryset(self.get_queryset())
        post, _ = self.get_object()

        service = CommentService(post=post, user=request.user)
        list_q = service.list_comments(comments=queryset)

        return  return_paginated_view(self, list_q)

    @action(methods=["post"], detail=True, url_path="comments")
    def create_replies(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        post, comment = self.get_object()
        data = serializer.validated_data
        try:
            service = CommentService(post, request.user)
            data.update({"parent": comment})
            nested_comment = service.create_nested_replies(**data)

        except Exception as e:
            sts = "failed"
            msg = str(e)
            code = 400
        else:
            sts = "success",
            msg = "Replies",
            code = 201

        if sts == "success":
            event = NotificationEvents.SYSTEM.value
            message = f"{request.user.user} commented on you comment"
            send_general_notification(
                sender=request.user,
                receiver=comment.user,
                message=message,
                event=event
            )
        return Response({"status": sts, "msg": msg}, status=code)

    @method_decorator(cache_page(60 * 5))
    @action(methods=['get'], detail=True, url_path="comments/list")
    def list_replies(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        post, comment_base = self.get_object()

        service = CommentService(post, request.user)
        comments = service.list_nested_comments(queryset, comment_base)

        return return_paginated_view(self, comments)
