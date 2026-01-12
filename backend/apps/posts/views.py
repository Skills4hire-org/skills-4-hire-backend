import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action

from django_filters.rest_framework import DjangoFilterBackend

from .models import Post, Comment
from .serializers import PostCreateSerializer, PostDetailSerializer, CommentSerializer
from .paginations import CustomPostPagination
from .permission import IsOwnerOrReadOnly

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
        serializer.save(user=self.request.user)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Wrap updates in a transaction and prefer partial updates where appropriate."""
        return super().update(request, *args, **kwargs)

    def perform_destroy(self, instance: Post):
        # Use soft delete to preserve data and indexes
        instance.soft_delete()

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



class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

    queryset = Comment.objects.filter(
        is_active=True, is_deleted=False
    ).select_related("users").prefetch_related("post_media")


    def get_queryset(self):
        return self.queryset.all()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        post_pk = self.kwargs.get("post_pk")
        
        if post_pk is None:
            logger.error("Post PK not found in URL kwargs for comment creation.")
            return Response(
                {"detail": "Post ID is required to create a comment."},
                status=status.HTTP_400_BAD_REQUEST
            )
        post_instance = get_object_or_404(Post, pk=post_pk, is_active=True, is_deleted=False)
        try:
            with transaction.atomic():
                comment_instance = serializer.save(post=post_instance, user=request.user)
        except Exception:
            logger.exception("Failed to create Comment")
            raise
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
        
    @action(methods=["post"], detail=True, url_path="replies")
    def replies(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        post_pk = self.kwargs.get("post_pk")
        if post_pk is None:
            logger.error("Post PK not found in URL kwargs for reply creation.")
            return Response(
                {"detail": "Post ID is required to create a reply."},
                status=status.HTTP_400_BAD_REQUEST
            )
        post_instance = get_object_or_404(Post, pk=post_pk, is_active=True, is_deleted=False)

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