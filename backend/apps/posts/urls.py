from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from .views import PostViewSet, CommentViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')

nested_router = NestedSimpleRouter(router, r"posts", lookup="posts")
nested_router.register(r"comment", CommentViewSet, basename="comment")
urlpatterns = [
    path('', include(router.urls)),
    path('', include(nested_router.urls))
]
