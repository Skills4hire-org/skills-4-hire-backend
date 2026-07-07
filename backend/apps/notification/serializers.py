from rest_framework import serializers

from .models import Notification
from ..authentication.serializers import UserReadSerializer

class NotificationReadSerializer(serializers.ModelSerializer):
    sender = UserReadSerializer(read_only=True)
    counts = serializers.SerializerMethodField()
    class Meta:
        model = Notification
        fields = [
            "notification_id", "sender", 
            "event", "content", 
            "created_at", "counts",
            "is_read"
        ]
    
    def get_counts(self, obj: Notification) -> int:
        notifications = Notification.objects.filter(receiver=obj.user, is_deleted=False)
        return notifications.count()
    