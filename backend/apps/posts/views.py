import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound

from django_filters.rest_framework import DjangoFilterBackend

from .models import Post, Comment, PostLike
from .serializers import PostCreateSerializer, PostDetailSerializer, CommentSerializer
from .paginations import CustomPostPagination
from .permission import IsOwnerOrReadOnly
from .utils.posts import get_post_by_id

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
        Post.objects.filter(is_active=True, is_deleted=False)
        .select_related('user')
        .prefetch_related('post_media', 'post_tag__service')
    )
    pagination_class = CustomPostPagination
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['post_type', 'user']
    search_fields = ['post_content']
    ordering_fields = ['created_at', 'updated_at']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PostCreateSerializer
        return PostDetailSerializer

    def get_queryset(self):
        # Ensure we always start from the base queryset to allow further
        # filtering by DRF filter backends.
        return self.queryset.all()

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        """List posts (cached for a short period)."""
        return super().list(request, *args, **kwargs)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create post as the authenticated user in a DB transaction."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except Exception:
            logger.exception('Failed to create Post')
            raise
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Wrap updates in a transaction and prefer partial updates where appropriate."""
        return super().update(request, *args, **kwargs)

    def perform_destroy(self, instance: Post):
        # Use soft delete to preserve data and indexes
        instance.soft_delete()

    @method_decorator(cache_page(60 * 15))
    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request):
        """Return the authenticated user's posts with normal pagination and filtering."""
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

        qs = self.filter_queryset(self.get_queryset().filter(user=request.user).order_by("-created_at"))
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(methods=["post"], detail=True, url_path="like")
    def like_post(self, request, *args, **kwargs):
        """
        Like a post.
        post_pk is expected in the URL kwargs.
        """ 
        post_pk = self.kwargs.get("post_id")
        post = get_post_by_id(post_pk.strip())
        if not post.get("success"):
            return Response(status=status.HTTP_404_NOT_FOUND, data={"detail":f"{post.get('msg')}"})

        try:
            with transaction.atomic():
                like = PostLike.objects.create(user=request.user, post=post["post"], is_active=True)
        
        except Exception as exc:
            logger.error(f"Failed to create a like for post {post_pk}: {exc}")
            raise
        
        return Response(f"Post {post_pk} liked successfully.", status=status.HTTP_201_CREATED)

    @action(methods=["delete"], detail=True, url_path="unlike")
    def unlike_post(self, request, *args, **kwargs):
        """
        Unlike a post.
        post_pk is expected in the URL kwargs.
        """
        post_pk = self.kwargs.get("post_id")
        post = get_post_by_id(post_pk.strip())  
        if not post.get("success"):
            return Response(status=status.HTTP_404_NOT_FOUND, data={"detail":f"{post.get('msg')}"})
        try:
            with transaction.atomic():
                like_instance = get_object_or_404(
                    PostLike,
                    user=request.user,
                    post=post["post"],
                    is_active=True
                )
                like_instance.soft_delete()
        except Exception as exc:
            logger.error(f"Failed to unlike post {post_pk}: {exc}")
            raise
        return Response(f"Post {post_pk} unliked successfully.", status=status.HTTP_200_OK)



class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

    pagination_class = CustomPostPagination

    queryset = (Comment.objects.filter(
            is_active=True, is_deleted=False
        ).select_related("user", "post", "parent").prefetch_related("post_media")
    )

    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        """ Filter comment for post in URL kwargs"""
        post_pk = self.kwargs.get("posts_pk")
        qs = self.queryset.all()
        if post_pk:
            post_instance = get_post_by_id(post_pk.strip())
            if not post_instance.get("success"):
                raise NotFound(detail=post_instance.get("msg") or "POST_NOT_FOUND")
            qs = qs.filter(post=post_instance.get("post"))
            return qs.order_by("-created_at")
        else:
            qs = qs.none()
            return qs

        
                        
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        print(self.kwargs)
        post_pk = kwargs.get("posts_pk")
        post = get_post_by_id(post_pk.strip())
        if not post.get("success"):
            return Response(status=status.HTTP_404_NOT_FOUND, data={"detail":f"{post.get('msg')}"})
        post_instance = post["post"]
        try:
            with transaction.atomic():
                comment_instance = serializer.save(post=post_instance)
        except Exception:
            logger.exception("Failed to create Comment")
            raise
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        obj = self.get_object()
        if not obj.can_edit(self.request.user):
            logger.warning(f"User {self.request.user} attempted to edit Comment {obj.pk} without permission.")
            raise PermissionError("You do not have permission to edit this comment.")
        serializer.save()

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    def perform_destroy(self, instance):
        if not instance.can_edit(self.request.user):
            logger.warning(f"User {self.request.user} attempted to delete Comment {instance.pk} without permission.")
            raise PermissionError("You do not have permission to delete this comment.")
        instance.soft_delete()

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        """List comments (cached for a short period)."""
        return super().list(request, *args, **kwargs)


    @action(methods=["post"], detail=True, url_path="replies")
    def replies(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        post_pk = self.kwargs.get("post_pk")
        post = get_post_by_id(post_pk.strip())
        if not post.get("success"):
            return Response(status=status.HTTP_404_NOT_FOUND, data={"detail":f"{post.get('msg')}"})
        post_instance = post["post"]
        comment_pk = self.kwargs.get("comment_id")
        if comment_pk is None:
            logger.error("Comment PK not found in URL kwargs for reply creation.")
            return Response(
                {"detail": "Comment ID is required to create a reply."},
                status=status.HTTP_400_BAD_REQUEST
            )
        parent_comment = get_object_or_404(Comment, pk=comment_pk, is_active=True, is_deleted=False)

        try:
            with transaction.atomic():
                reply_instance = serializer.save(
                    post=post_instance,
                    parent=parent_comment,
                    user=request.user
                )
        except Exception:
            logger.exception("Failed to create Reply")
            raise
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers) 