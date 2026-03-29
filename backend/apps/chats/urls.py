from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from .views import (
    ConversationViewSet, NegotiationViewSet,
    MessageViewSet
)
from .endorsements.urls import endorsement_urlpatterns

router = DefaultRouter()

router.register(r'conversation', ConversationViewSet, basename="conversation")
router.register("negotiation", NegotiationViewSet, basename="negotiation")

message_routers = NestedSimpleRouter(parent_router=router, parent_prefix="conversation", lookup="conversation")
message_routers.register("messages", MessageViewSet, basename="messages")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(message_routers.urls))

]

urlpatterns += endorsement_urlpatterns
