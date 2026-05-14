from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from .views import (
    ConversationViewSet,
    NegotiationViewSet,
    MessageViewSet,
    OpenSupportRoomView,
    SupportInboxView,
    MarkMessagesReadView,
    SupportRoomMessagesView,
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

# Support URLs
urlpatterns += [
    path('support/open/',
         OpenSupportRoomView.as_view(),
         name='support-open'),

    path('support/inbox/',
         SupportInboxView.as_view(),
         name='support-inbox'),

    path('support/read/',
         MarkMessagesReadView.as_view(),
         name='support-mark-read'),

    path('support/<uuid:room_id>/messages/',
         SupportRoomMessagesView.as_view(),
         name='support-messages'),
]

urlpatterns += endorsement_urlpatterns
