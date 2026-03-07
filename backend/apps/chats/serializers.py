from rest_framework import serializers
from rest_framework.exceptions import  NotFound

from django.utils.text import gettext_lazy as _
from .models import  Conversation
from  apps.posts.services import get_post_by_id, Post
from apps.authentication.helpers import get_user_by_pk
from .services.conversations import ConversationService

class ConversationCreateSerializer(serializers.ModelSerializer):
    receiver_id = serializers.UUIDField(required=True)

    class Meta:
        model = Conversation
        fields = [
            "receiver_id",
        ]

    def create(self, validated_data):
        receiver_id = validated_data["receiver_id"]

        user = self.context.get("request")["user"]
        try:
            receiver = get_user_by_pk(receiver_id)
        except NotFound as e:
            raise serializers.NotFound(_(str(e)))

        try:
            services = ConversationService(
                sender=user,
                receiver=receiver,
            )
            new_conversation = services.create_conversation(**validated_data)
        except Exception as e:
            raise serializers.ValidationError(_("Error creating conversation"))

        return  new_conversation






