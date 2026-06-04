import logging
from typing import Any

from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import Model, Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import viewsets, status, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView


from .models import Post, Comment, UserPostInteraction, Repost
from .serializers.create import (
    PostCreateSerializer, RepostSerializer, CommentCreateSerializer
)
from .serializers.read import (
    GeneralPostSerializer, ServicePostSerializer, JobPostSerializer,
    CommentListSerializer, PostDetailSerializer, RepostListSerializer
)
from .serializers.feed_serializer import FeedPostSerializer

from .paginations import CustomPostPagination
from .permission import IsOwnerOrReadOnly
from .utils.posts import get_post_by_id
from .services_T import  (
    return_paginated_view, LikeService,
    CommentService,
    get_offers_or_job_post, list_posts
)
from .services.recommendation_service import RecommendationService
from apps.bookings.permissions import  IsCustomer

import uuid

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
        .select_related('user')
        .prefetch_related('attachments', 'tags', "comments", "repost_records", "likes")
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
        if self.action in ("list", "retrieve", "user_posts"):
            if user.is_provider:
                return JobPostSerializer
            else:
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
        user = self.request.user

        queryset = self.filter_queryset(self.queryset)
        updated_qs = queryset.annotate(
            comments_counts=Count("comments", filter=Q(comments__is_active=True), distinct=True),
            likes_count=Count("likes", filter=Q(likes__is_active=True), distinct=True),
            reposts_count=Count("repost_records", filter=Q(repost_records__is_active=True), distinct=True)
        ).order_by("-created_at")

        if "include_offers" in self.request.query_params:
            include_offers = self.request.query_params['include_offers']
            updated_qs = get_offers_or_job_post(user, updated_qs, include_offers)

        if "include_mine" in self.request.query_params:
            include_mine = self.request.query_params['include_mine']
            if include_mine:
                updated_qs = list_posts(user, updated_qs)
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
        post = self.get_object()
        try:
            reposts = Repost.objects.filter(
                original_post=post).select_related(
                    "reposted_by").only(
                        "repost_id", "reposted_by", "comment").order_by("-created_at")
            
        except Exception as e:
            return  Response({"status": "failed", "msg": str(e)}, status=400)
        return  return_paginated_view(self, reposts)

    @action(methods=['get'], detail=False, url_path="user/(?P<user_id>[^/.]+)/posts")
    def user_posts(self, request, user_id: uuid.UUID = None):
        queryset = self.filter_queryset(self.get_queryset())
        if user_id is None:
            return Post.objects.none()
        qs = queryset.filter(user__pk=user_id)
        return return_paginated_view(self, qs)
    

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

        comment_instance = None
        if comment_pk is not None:
            comment_instance = get_object_or_404(Comment, pk=comment_pk, is_active=True)

        post = get_post_by_id(post_pk)
        if not post.get("success"):
            return False

        post_instance = post.get("post")

        return  post_instance, comment_instance

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        post, _ = self.get_object()

        serializer = self.get_serializer(
            data=request.data, 
            context={"request": request, "post": post}
        )
        serializer.is_valid(raise_exception=True)
        try:
            comment = serializer.save()
            return  Response({"status": True, "detail": CommentListSerializer(comment).data }, status=201)
        except Exception as e:
            return Response({"status": False, "details": str(e)}, status=400)
        
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

    @method_decorator(cache_page(60))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @method_decorator(cache_page(60))
    def retrieve(self, request, *args, **kwargs):
        _, comment = self.get_object()
        serializer = self.get_serializer(comment)
        return Response({"status": True, "details": serializer.data}, status=200)

    @action(methods=["post"], detail=True, url_path="replies")
    def create_replies(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        post, comment = self.get_object()
        data = serializer.validated_data
        service = CommentService()
        try:
            new_comment = service.add_comment(post=post, parent=comment, user=user, message=data['message'])
            return Response({"status": True, "details": CommentListSerializer(new_comment).data}, status=201)

        except Exception as e:
            return Response({"status": False, "details": str(e)}, status=400)

    @method_decorator(cache_page(60))
    @action(methods=['get'], detail=True, url_path="list-replies")
    def list_replies(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        post, comment_base = self.get_object()
        nested_comments = queryset.filter(parent=comment_base)
        return return_paginated_view(self, nested_comments)

class CommentLikeViewSet(viewsets.GenericViewSet):

    http_method_names = ["post", "delete", "get"]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPostPagination

    def get_object(self):
        comment_id = self.kwargs.get("pk")
        comment = get_object_or_404(Comment, pk=comment_id, is_active=True)

        return comment

    def get_serializer_class(self):
        if self.action == "user_comments":
            return CommentListSerializer

    @method_decorator(cache_page(60))
    @action(methods=['get'], detail=False, url_path="user/(?P<user_id>[^/.]+)/comments")
    def user_comments(self, request, user_id: uuid.UUID=None):
        user = get_object_or_404(User, pk=user_id, is_active=True, is_verified=True)
        comments = user.comments.filter(is_active=True)
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = CommentListSerializer(comments, many=True, context={'request': request})
        return Response(data=serializer.data, status=200)
    

    @action(methods=["POST"], detail=True, url_path='like')
    def like_comment(self, request, *args, **kwargs):
        comment = self.get_object()

        like_service = LikeService()
        try:   
            with transaction.atomic():
                like = like_service.like_comment(comment, request.user)

            return Response({"status": True, "details": f"Liked comment with id: {str(comment.pk)}"})
        except Exception as exc:
            return Response({"status": False, "details": str(exc)}, status=400)


    @action(methods=['DELETE'], detail=True, url_path="unlike")
    def unlike_comment(self, request, *args, **kwargs):
        comment  = self.get_object()
        like_service = LikeService()
        try:
            like = like_service.unlike_comment(comment, request.user)

            return Response(status=204)
        except Exception as exc:
            return Response({"status": True, "details": str(exc)})

class FeedListView(ListAPIView):
    """
    API endpoint for the personalized post feed with multi-signal recommendations.
    
    GET /api/posts/feed/
    
    Supports the following query parameters:
    - category: Filter candidates by category slug
    - location: Override user's location for relevance matching
    - page: Pagination page number (default 1)
    - limit: Results per page (default 20, max 50)
    - exclude_seen: Whether to skip already-viewed posts (default true)
    
    Returns:
    - List of recommended posts ordered by recommendation score
    - Each post includes creator trust_score and recommendation_score for transparency
    
    Authentication: Required (IsAuthenticated)
    
    Example:
        GET /api/posts/feed/?category=plumbing&location=Lagos&limit=20
    """
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FeedPostSerializer
    pagination_class = CustomPostPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "amount", "post_type", "country", "state", "city",
        "post_title", "tags__name", ""
    ]
    
    def get_queryset(self):
        """
        This method is overridden to return an empty QuerySet because we're
        building a list dynamically from the recommendation service rather
        than using a standard Django QuerySet.
        """
        return Post.objects.none()
    
    def list(self, request, *args, **kwargs):
        """
        Override list() to use the recommendation service instead of standard queryset filtering.
        
        Args:
            request: HTTP request with optional query parameters
            
        Returns:
            Response with paginated list of recommended posts
        """
        # Parse query parameters
        category = request.query_params.get('category', None)
        location = request.query_params.get('location', None)
        exclude_seen = request.query_params.get('exclude_seen', False)
        include_offers = request.query_params.get('include_offers', False)
        
        try:
            limit = min(int(request.query_params.get('limit', 20)), 50)
            page = max(int(request.query_params.get('page', 1)), 1)
            offset = (page - 1) * limit
        except (ValueError, TypeError):
            limit = 20
            offset = 0
        
        # Get recommendation service instance
        recommendation_service = RecommendationService(user=request.user)
        
        # Generate feed
        try:
            feed_posts = recommendation_service.get_feed(
                category=category,
                location=location,
                exclude_seen=exclude_seen,
                include_offers=include_offers,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Error generating feed for user {request.user.id}: {e}")
            return Response(
                {'error': 'Failed to generate feed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Record a 'view' interaction for each post in the feed
        # (This tracks feed impressions for algorithm improvement)
        self._record_feed_impressions(request.user, feed_posts)
        
        # Serialize the results with recommendation scores
        filtered_post = self.filter_queryset(feed_posts)
        page = self.paginate_queryset(filtered_post)
        serialized_posts = []
        for item in page:
            post = item['post']
            recommendation_score = item['score']
            
            serializer = FeedPostSerializer(
                post,
                context={
                    'request': request,
                    'recommendation_score': recommendation_score
                }
            )
            serialized_posts.append(serializer.data)

        return self.get_paginated_response(serialized_posts)
    
    def _record_feed_impressions(self, user, feed_posts: list):
        """
        Record 'view' interactions for posts shown in the feed.
        
        This helps track which posts were shown to the user, enabling
        better algorithm training and engagement metrics.
        
        Args:
            user: User who viewed the feed
            feed_posts: List of dicts with 'post' key
        """
        try:
            for item in feed_posts:
                post = item['post']
                # Only create if not already exists (unique constraint)
                UserPostInteraction.objects.get_or_create(
                    user=user,
                    post=post,
                    interaction_type=UserPostInteraction.InteractionType.VIEW,
                    defaults={'created_at': timezone.now()}
                )
                
        except Exception as e:
            # Don't fail the feed request if impression tracking fails
            logger.warning(f"Failed to record feed impressions for user {user.id}: {e}")

class PostInteractionViewSet(viewsets.ViewSet):
    """
    ViewSet for recording user interactions with posts.
    
    POST /api/posts/{post_id}/interact/
    
    Request body:
    {
        "interaction_type": "view|like|comment|repost",
        "comment": "optional text for reposts"
    }
    
    Records interactions that feed into:
    - Feed exclusion logic (skip already-viewed posts)
    - Relevance scoring (past behavior)
    - Engagement count updates (for ranking)
    
    Returns:
    {
        "status": "success",
        "interaction_id": "uuid",
        "interaction_type": "like",
        "message": "Interaction recorded"
    }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'], url_path='interact')
    def interact(self, request, post_id=None):
        """
        Record a user interaction with a post.
        
        Args:
            request: HTTP POST request
            post_id: UUID of the post being interacted with
            
        Returns:
            Response with interaction details
        """
        # Get the post
        post = get_object_or_404(Post, post_id=post_id)
        
        # Get interaction type from request
        interaction_type = request.data.get('interaction_type', None)
        if interaction_type not in [choice[0] for choice in UserPostInteraction.InteractionType.choices]:
            return Response(
                {'error': f'Invalid interaction_type: {interaction_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Record the interaction
                interaction, created = UserPostInteraction.objects.update_or_create(
                    user=request.user,
                    post=post,
                    interaction_type=interaction_type,
                    defaults={'created_at': timezone.now()}
                )
                
                # Handle repost-specific logic
                if interaction_type == UserPostInteraction.InteractionType.REPOST:
                    comment = request.data.get('comment', '')
                    repost, repost_created = Repost.objects.update_or_create(
                        original_post=post,
                        reposted_by=request.user,
                        defaults={'comment': comment}
                    )
                
                # Update post engagement count
                self._update_engagement_count(post)
                
                return Response({
                    'status': 'success',
                    'interaction_id': str(interaction.interaction_id),
                    'interaction_type': interaction_type,
                    'message': f'Interaction recorded: {interaction_type}',
                    'created': created
                }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error recording interaction for user {request.user.id}, post {post_id}: {e}")
            return Response(
                {'error': 'Failed to record interaction'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def _update_engagement_count(post: Post):
        """
        Update the post's engagement_count to reflect current likes, comments, reposts.
        
        Called after any interaction to keep the count synchronized.
        This can also be called via signals or periodic tasks.
        
        Args:
            post: Post instance to update
        """
        try:
            likes_count = post.likes.filter(is_active=True).count()
            comments_count = post.comments.filter(is_active=True).count()
            reposts_count = post.repost_records.filter(is_active=True).count()
            
            engagement = likes_count + comments_count + reposts_count
            post.engagement_count = engagement
            post.save(update_fields=['engagement_count'])
            
        except Exception as e:
            logger.error(f"Error updating engagement count for post {post.post_id}: {e}")
