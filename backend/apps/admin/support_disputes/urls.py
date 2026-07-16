from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SupportViewsets, ConversationViewsets

router = DefaultRouter()
router.register("supports", SupportViewsets, basename="admin-support")
router.register("conversations", ConversationViewsets, basename="admin-convesations")

support_urlpatterns = [
    path("", include(router.urls))
]