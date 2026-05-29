from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet

notification_router = DefaultRouter()
notification_router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(notification_router.urls)),
]