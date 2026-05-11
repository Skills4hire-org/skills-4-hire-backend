import logging
from typing import Any

from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import Model, Count, Q

from rest_framework import viewsets, status, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied


from .models import Post, Comment
from .serializers.create import (
    PostCreateSerializer, RepostSerializer, CommentCreateSerializer
)
from .serializers.read import (
    GeneralPostSerializer, ServicePostSerializer, JobPostSerializer,
    CommentListSerializer, PostDetailSerializer, RepostListSerializer
)

from .paginations import CustomPostPagination
from .permission import IsOwnerOrReadOnly, IsComentOwner
from .utils.posts import get_post_by_id
from .services import  (
    return_paginated_view, LikeService,
    CommentService, list_nested_reposts,
    get_offers_or_job_post, list_posts
)
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
        Post.is_active_objects.filter(is_deleted=False)
        .select_related('user', "parent")
        .prefetch_related('attachments', 'tags')
    )
    pagination_class = CustomPostPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "post_type": ["icontains"],
        "user__profile__display_name": ["icontains"],
        "amount": ["gte", 'lte'],
        "post_content": ["icontains"]
    }
    search_fields = ['post_title', "tags__name"]
    ordering_fields = ['-created_at', '-updated_at']

    def get_serializer_class(self):

        user = self.request.user

        if self.action in ('create', 'update', 'partial_update'):
            return PostCreateSerializer
        if self.action in ("list", "retrieve"):
            if user.is_provider:
                return JobPostSerializer
            else:
                return PostDetailSerializer  
        if self.action == "offers":
            return JobPostSerializer
        
        if self.action == "mine":
            return PostDetailSerializer
        
        if self.action == 'repost_post':
            return RepostSerializer
        if self.action == "get_reposts":
            return RepostListSerializer
    
    def get_permissions(self):
        if self.action == "offers":
            return [IsCustomer()]
        elif self.action in ("like_post", "unlike_post", "repost_post"):
            return [permissions.IsAuthenticated()]
        return [IsOwnerOrReadOnly()]

    def get_queryset(self):
        # Ensure we always start from the base queryset to allow further filtering by DRF filter backends.
        queryset = self.filter_queryset(self.queryset)

        updated_qs = queryset.annotate(
            comments_counts=Count("comments", filter=Q(comments__is_active=True), distinct=True),
            likes_count=Count("likes", filter=Q(likes__is_active=True), distinct=True),
            reposts_count=Count("reposts", filter=Q(reposts__is_active=True), distinct=True)
        ).order_by("-created_at")

        current_user = self.request.user

        # if current_user.is_provider and self.action == "list":
        #     updated_qs = updated_qs.filter(post_type__in=[Post.PostType.JOB, Post.PostType.GENERAL])

        # if current_user.is_customer and self.action == "list":
        #     updated_qs = updated_qs.filter(post_type__in=[Post.PostType.GENERAL, Post.PostType.SERVICE])

        return updated_qs

    def list(self, request, *args, **kwargs):
        """List posts (cached for a short period)."""
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return  super().retrieve(request, *args, **kwargs)

    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        """Create post as the authenticated user in a DB transaction."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        post_type = validated_data['post_type']
        try:
            saved_instance = serializer.save()
            
            return_instance = None
            
            if post_type == Post.PostType.GENERAL:
                return_instance = GeneralPostSerializer(saved_instance)
            elif post_type == Post.PostType.SERVICE:
                return_instance = ServicePostSerializer(saved_instance)
            else: 
                return_instance = JobPostSerializer(saved_instance)

        except Exception as e:
            logger.info(str(e))
            sts: str = "Failed"
            msg = str(e)
            code = status.HTTP_400_BAD_REQUEST
        else:
            sts: str = "success"
            msg="Post created"
            code = status.HTTP_201_CREATED

        return  Response(
            data={"status": sts, "msg": msg, "detail": return_instance.data}, status=code
        )

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

    @method_decorator(cache_page(60))
    @action(detail=False, methods=["get"], url_path="offers")
    def offers(self, request, include_offers: bool = True, *args, **kwargs):
        """ Returns customer jobs posts with pagination"""

        queryset = get_offers_or_job_post(
            user=request.user,
            queryset=self.filter_queryset(self.get_queryset()),
            include_offers=include_offers
        )

        return return_paginated_view(self, queryset)

    @method_decorator(cache_page(60))
    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request, *args, **kwargs):
        """Return the authenticated user's posts with normal pagination and filtering."""
        queryset = list_posts(request.user, self.filter_queryset(self.get_queryset()))
        return return_paginated_view(self, queryset)

    @action(methods=["post"], detail=True, url_path="like")
    def like_post(self, request, *args, **kwargs):
        """
        Like a post.
        post_pk is expected in the URL kwargs.
        """
        post = self.get_object()
        user = request.user
        try:
            like_post = LikeService()
            new_like = like_post.create_like_post(post, user)
        except Exception as exc:
            logger.error(f"Failed to create a like for post {post.pk}: {exc}")
            sts = False
            msg = str(exc)
            code=400
        else:
            sts = "success"
            msg = f"liked post: {post.pk}"
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
            like_post = LikeService()
            new_like = like_post.unlike_post(post, request.user)
        except Exception as exc:
            logger.error(f"Failed to unlike post {post.pk}: {exc}")
            msg= str(exc)
            sts = "failed"
            code=400
        else:
            msg="Unliked Post: "+ str(post.pk),
            sts="success",
            code=200
        return Response({"status": sts, "msg": msg}, status=code)


    @action(methods=["post"], detail=True, url_path="repost")
    def repost_post(self, request, *args, **kwargs):
        post_instance = self.get_object()

        serializer = self.get_serializer(
            data=request.data, context={
                'post': post_instance, "request": request
                }
        )
        serializer.is_valid(raise_exception=True)

        try:
            repost = serializer.save()
            return Response({"status": True, "details": RepostListSerializer(repost).data}, status=201)
        except Exception as e:
            logger.info(str(e))
            msg = str(e)
            sts = "failed"
            code = 400  
        return Response({"status": sts, "message": msg}, status=code)
        
    @method_decorator(cache_page(timeout=60 * 5))
    @action(methods=['get'], url_path="reposts", detail=True)
    def get_reposts(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        post = self.get_object()
        try:
            reposts = list_nested_reposts(post, queryset)
        except Exception as e:
            return  Response({"status": "failed", "msg": str(e)}, status=400)
        return  return_paginated_view(self, reposts)

class CommentViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPostPagination

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'create_replies'):
            return CommentCreateSerializer
        else:
            return CommentListSerializer

    permissions = [IsOwnerOrReadOnly]

    def get_queryset(self):
        """ return base queryset"""
        post_instance, _ = self.get_object()
        queryset = (
            Comment.active_objects.filter(post=post_instance).
                    select_related("post", "user", 'parent').prefetch_related('attachments')
                    )

        return queryset.annotate(
            total_replies=Count("replies", filter=Q(replies__is_active=True), distinct=True),
            total_likes=Count("likes", filter=Q(likes__is_active=True), distinct=True)
        )

    def get_object(self) -> bool | tuple[Any, Model | Any]:
        post_pk = self.kwargs.get("posts_pk")
        comment_pk = self.kwargs.get('pk')

        if comment_pk is not None:
            comment_instance = super().get_object()


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
            raise PermissionDenied()
        instance.soft_delete()

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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
        nested_comments = queryset.filter(parent=comment_base).all()
        return return_paginated_view(self, nested_comments)
