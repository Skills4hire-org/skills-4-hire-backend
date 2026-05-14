from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from .views import PostViewSet, CommentViewSet, CommentLikeViewSet, FeedListView, PostInteractionViewSet

# Standard router for posts, comments, and likes
router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')
router.register(r"comments", CommentLikeViewSet, basename='likes')
router.register(r'posts', PostInteractionViewSet, basename='post-interact')

# Nested router for post comments
nested_router = NestedSimpleRouter(router, r"posts", lookup="posts")
nested_router.register(r"comment", CommentViewSet, basename="comment")

urlpatterns = [
    # Personalized feed endpoint with multi-signal ranking
    path('posts/feed/', FeedListView.as_view(), name='feed-list'),
    
    path('', include(router.urls)),
    path('', include(nested_router.urls))
]
