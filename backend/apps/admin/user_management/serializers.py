from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg


UserModel = get_user_model()

class UserManagementListSerializer(serializers.ModelSerializer):
    referral_count = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = [
            "user_id", "email", 
            "phone", "first_name", 
            "last_name", "active_role",
            "login_provider", "is_active", 
            "is_provider", "is_customer",
            "is_verified", "created_at",
            "referral_count"
        ]

    def get_referral_count(self, obj):
        referrals = obj.referrals_made.count()
        return referrals
    
class UserManagementDetailSerializer(UserManagementListSerializer):
    recent_referrals = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta(UserManagementListSerializer.Meta):
        model = UserManagementListSerializer.Meta.model
        fields = UserManagementListSerializer.Meta.fields + ["recent_referrals", "avg_rating"]

    def get_recent_referrals(self, obj):
        referrals = obj.referrals_made.all().order_by("-created_at")[:5]
        referred_users = [referral.referred for referral in referrals]
        return UserManagementListSerializer(referred_users, many=True, context=self.context).data
    
    def get_avg_rating(self, obj):
        if obj.is_provider:
            provider_profile = obj.profile.provider_profile
            rating = provider_profile.reviews.filter(is_active=True).aggregate(rating=Avg("ratings"))
            return rating['rating']
        else:
            return 0