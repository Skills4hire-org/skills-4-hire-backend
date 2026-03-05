from rest_framework import serializers

from .models import Notification
from ..authentication.serializers import UserReadSerializer

class NotificationReadSerializer(serializers.ModelSerializer):
    user = UserReadSerializer(read_only=True)
    counts = serializers.SerializerMethodField()
    class Meta:
        model = Notification
        fields = [
            "notification_id", "user",
            "event", "content",
            "created_at", "counts",
            "is_read"
        ]
    
    def get_counts(self, obj: Notification) -> int:
        notifications = Notification.objects.filter(user=obj.user, is_deleted=False)
        return notifications.count()
    