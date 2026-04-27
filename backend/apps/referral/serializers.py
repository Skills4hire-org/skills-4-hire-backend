from django.conf import settings
from django.db import transaction

from rest_framework import serializers

from .models import Referral, ReferralCode, ReferralTransactions
from .services_T import TransactionService
from ..wallet.services import BankAccountService
from ..wallet.paystack.service import PaystackError, PaystackService
from .services.utils import generate_reference_key
from .tasks import process_transfer_task

import logging

logger = logging.getLogger(__name__)

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
        user_referrals_count = obj.owner.referrals_made.filter(
            status__in=[Referral.Status.PENDING, Referral.Status.CONVERTED]
            ).count()
        
        return float(user_referrals_count * commision)

class ReferralWithdrawalSerializer(serializers.ModelSerializer):

    payment_recipient_code = serializers.CharField(required=True, write_only=True)
    class Meta: 
        model = ReferralTransactions
        fields = [
            "amount", "idempotency_key",
            'payment_recipient_code'
        ]

    def validated_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("amount must be positive")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user

        amount = validated_data['amount']
        transation_service = TransactionService()

        referrals = transation_service.process_total_referrals(user)
        if not referrals['status']:
            raise serializers.ValidationError(referrals['message'])
        
        total_referrals = referrals['total']
        process_amount = transation_service.process_referrals_amount(amount, total_referrals)

        if not process_amount['status']:
            raise serializers.ValidationError(process_amount['message'])
        
        recipient_code = validated_data.pop('payment_recipient_code')
        reference_key = generate_reference_key(user)
        
        total_to_reward = process_amount['total_to_reward']
        referrals = Referral.objects.filter(
            status=Referral.Status.CONVERTED, referrer=user
        )[:total_to_reward]

        try:
            validated_data['reference_key'] = reference_key
            validated_data['user'] = user
            validated_data['referrals'] = referrals

            with transaction.atomic():
                referral_transaction = transation_service.create_transaction(validated_data)

        except Exception as exc:
            logger.error(exc)
            raise serializers.ValidationError(exc)
        
        transaction_instance = referral_transaction['instance']

        bank_service = BankAccountService()
        bank = bank_service.get_account_by_recipient_code(recipient_code)
        if not bank['status']:
            raise serializers.ValidationError(bank['message'])
        bank_account = bank['instance']
        process_transfer_task.delay(transaction_instance.transaction_id, bank_account.recipient_code)

        return transaction_instance
    
class ReferralWithdrawalListSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReferralTransactions
        fields = [
            "transaction_id", 'user',
            'amount', 'reference_key', 
            'idempotency_key', 'created_at',
            'transfer_code', "is_active", 
            'status', 'completed_at', 'failed_at',
            'reversed_at'
        ]
