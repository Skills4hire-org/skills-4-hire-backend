from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.posts.views import PostViewSets
router = DefaultRouter()
router.register(r'posts', PostViewSets, basename='posts')

urlpatterns = [
    path('', include(router.urls)),
]
