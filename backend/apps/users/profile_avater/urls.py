from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import AvatarViewSet

router = DefaultRouter()

router.register("avatar", AvatarViewSet, basename="avatar")

avatar_urlpatterns = [
    path('', include(router.urls))
]