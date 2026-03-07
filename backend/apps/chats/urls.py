from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ConversationViewSet

conversation_router = DefaultRouter()

conversation_router.register(r'conversation', ConversationViewSet, basename="conversation")

urlpatterns = [
    path("", include(conversation_router.urls)),
]

