from .models import Referral, ReferralTransactions, UserModel

from django.conf import settings
from django.utils import timezone
from django.db import transaction

commision = settings.REFERRAL_COMMISION

class TransactionService:

    def __init__(self):
        pass

    def process_total_referrals(self, user: UserModel):
        if not user:
            return {"status": False, "message": "invalid user object or empty"}
        
        user_referrals = Referral.objects.filter(
                referrer=user, status=Referral.Status.CONVERTED
            )
        return { "status": True, "total": user_referrals.count()}
    
    def process_referrals_amount(self, amount, num_of_referrals):
        if amount < commision:
            return {"status": False, "message": "amount must not me less than "+ commision}
        
        if amount % commision != 0:
            return {"status": False, 'message': "amount must be in multiples of "+ commision}
        
        if amount > num_of_referrals * commision:
            return { "status": False, "message": "Insufficient Balance"}
        
        total_referrals_to_reward = amount / commision
        return {"status": True, "message": "validated", "total_to_reward": total_referrals_to_reward}
    
    def create_transaction(self, validated_data):

        if not validated_data['referrals'] or not validated_data['user']:
            return { "status": False, "message": "referrals and user must be present"}
        with transaction.atomic():
            try:
                reference_key = validated_data.pop('reference_key')
                referrals = validated_data.pop("referrals")
                transaction_instance, created = ReferralTransactions.objects.get_or_create(
                    reference_key=reference_key,
                    defaults=validated_data
                )

                transaction_instance.referrals.set(referrals)
            except Exception as exc:
                raise
    
        return {"status": True, "instance": transaction_instance}
    
    def process_completed_transaction(self, transaction_instance):
        if not isinstance(transaction_instance, ReferralTransactions):
            return {"status": False, "message": "not a valid instance"}
        
        with transaction.atomic():
            transaction_instance.status = ReferralTransactions.Status.COMPLETED
            transaction_instance.completed_at = timezone.now()

            referrals = transaction_instance.referrals.all()
            for referral in referrals:
                referral.status = Referral.Status.REWARDED
                referral.rewarded_at = timezone.now()

            Referral.objects.bulk_update(referrals, ['status', 'rewarded_at'])
            transaction_instance.save(update_fields=['status', 'completed_at'])

        return { "status": True, "message": "updated"}

    def process_failed_transaction(self, transaction_instance):
        if not isinstance(transaction_instance, ReferralTransactions):
            return {"status": False, "message": "not a valid instance"}
        with transaction.atomic():
            transaction_instance.status = ReferralTransactions.Status.FAILED
            transaction_instance.failed_at = timezone.now()
            transaction_instance.save(update_fields=['status', 'failed_at'])
        return {'status': False, "message": "updated"}
    
    def process_reversed_transaction(self, transaction_instance):
        if not isinstance(transaction_instance, ReferralTransactions):
            return {"status": False, "message": "not a valid instance"}
        with transaction.atomic():
            transaction_instance.status = ReferralTransactions.Status.REVERSED
            transaction_instance.reversed_at = timezone.now()
            transaction_instance.save(update_fields=['status', 'reversed_at'])
        return {'status': False, "message": "updated"}