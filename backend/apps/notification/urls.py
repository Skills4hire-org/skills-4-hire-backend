from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .test_websocket import test_websocket, index
from .views import NotificationViewSet

notification_router = DefaultRouter()

notification_router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(notification_router.urls)),
    path("websocket/", index, name="websocket"),
    path("send/message/", test_websocket, name="test")
]