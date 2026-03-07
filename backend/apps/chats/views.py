
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from .serializers import ConversationCreateSerializer
from .permissions import ConversationOwner
from .models import Conversation

from django.db.models import Q

class ConversationViewSet(viewsets.ModelViewSet):

    http_method_names = ["post", "get", "delete"]

    permission_classes =  [ConversationOwner]

    def get_queryset(self):
        user = self.request.user
        queryset = Conversation.active_objects.filter(
            Q(sender=user)|
            Q(receiver=user)
        ).select_related("sender", "receiver")

    def get_serializer_class(self):
        if self.action == "create":
            return  ConversationCreateSerializer

        return  None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(dataclasses=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except Exception as e:
            sts = "failed"
            msg = str(e)
            code = 400
        else:
            sts = "success"
            msg = "conversation_created"
            code = 201
        return  Response({"status": sts, "msg": msg}, status=code)








