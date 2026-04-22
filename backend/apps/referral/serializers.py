from django.conf import settings
from django.db.models import Count

from rest_framework import serializers
from .models import Referral, ReferralCode


base_url = settings.BASE_URL
commision = settings.REFERRAL_COMMISION

# class ReferralSerializer(serializers.ModelSerializer):
#     

#     class Meta: 
#         model = Referral
#         fields = [
#             "created", ""
#         ]

#     def get_balance(self, obj):
#         total_referrals  = obj.aggregate(total=Count("referral_id", distinct=True))
        
class ReferralCodeSerializer(serializers.ModelSerializer):
    referral_link = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    total_referrals = serializers.SerializerMethodField()

    class Meta:
        model = ReferralCode
        fields = [ "code", "referral_link", "created_at",
                  "balance", "total_referrals"]

    def get_referral_link(self, obj):
        return f"{base_url}api/v1/auth/register/?ref={obj.code}"
    
    def get_total_referrals(self, obj):
        user = obj.owner
        return user.referrals_made.count()
    
    def get_balance(self, obj):
        total_referrals = self.get_total_referrals(obj)
        return float(total_referrals * commision)



