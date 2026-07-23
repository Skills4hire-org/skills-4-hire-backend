from rest_framework import serializers

from ...bookings.models import Bookings
from ...authentication.serializers import UserReadSerializer

class AdminBookingListSerializer(serializers.ModelSerializer):
    customer = UserReadSerializer(read_only=True)
    provider = serializers.SerializerMethodField()

    class Meta:
        model = Bookings
        fields = [
            "booking_id", "booking_status",
            "customer", "provider", "location",
            "is_remote", "currency", "price", 
            "platform_fee", "is_active", "created_at"
        ]

    def get_provider(self, obj):
        user = obj.provider.profile.user
        return UserReadSerializer(user, read_only=True).data
    
    
