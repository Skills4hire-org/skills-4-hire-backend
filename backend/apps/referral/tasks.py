import celery
import logging

from django.db.models import Q
from django.db import transaction
from django.conf import settings

from ..bookings.services import BookingService, Bookings
from .models import Referral, ReferralTransactions
from ..wallet.paystack.service import PaystackService
from .services_T import TransactionService
from .services.referral_services import ReferralService


CONVERSATION_TRESHOLD = settings.CONVERSATION_TRESHOLD


logger = logging.getLogger(__name__)

@celery.shared_task(bind=True, max_retries=3, reject_on_worker_lost=True)
def process_referral_attchement(self, referred_user, code_str):
    try:
        service = ReferralService()
        worker = service.attach_referral(referred_user=referred_user, code_str=code_str)
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

def process_referral_conversion():

    logger.info("Processing Task: Auto updating Referral status")

    rewarded_bookings = BookingService.fetch_rewarded_booking()

    for booking in rewarded_bookings:
        if booking.booking_status != Bookings.BookingStatus.COMPLETED:
            logger.warning(
                "Skipping Rewarded Booking - Unexpected booking Status"
            )
            continue

        provider_user = booking.provider.profile.user
        customer = booking.customer

        pending_referrals = (
                    Referral.objects.select_related(
                        "referrer"
                        ).filter(
                            Q(referred=provider_user) |
                            Q(referred=customer),
                            status=Referral.Status.PENDING
                        )
        )

        for referral in pending_referrals:
            referred = referral.referred

            completed_booking_count = (
                Bookings.objects.filter(
                    Q(customer=referred)|
                    Q(provider=referred.profile.provider_profile),
                    booking_status=Bookings.BookingStatus.COMPLETED
                ).count()
            )
            entitled_conversation = completed_booking_count // CONVERSATION_TRESHOLD

            if entitled_conversation > 0:

                user_pending_referral_ids = Referral.objects.select_related(
                       "referrer"
                       ).filter(
                           referred=referred,
                           status=Referral.Status.PENDING
                        ).values_list("referral_id", flat=True)[:entitled_conversation]
                
                
                Referral.objects.filter(referral_id__in=list(user_pending_referral_ids)).update(
                    status=Referral.Status.CONVERTED
                )
                logger.info(f"Converted {len(list(user_pending_referral_ids))} pending referral.")

@celery.shared_task(bind=True, max_retries=3)
def process_referral_conversion_task(self):
    try:
        process_referral_conversion()
    except Exception as exc:
        logger.error("Referral conversion task failed: %s", exc)
        raise self.retry(exc=exc, countdown=60 * 5) 
    
def process_transfer(transaction_id, recipient_code):
    logger.info(
        "Processing Task for transfer verification for referral %s", transaction_id
    )
    with transaction.atomic():
        try:
            referral_transaction = (
                ReferralTransactions.objects
                .select_related("user").prefetch_related("referrals")
                .get(transaction_id=transaction_id)
            )
        except ReferralTransactions.DoesNotExist:
            logger.error("Transaction does not exitst")
            return { "status": False, "message": "transaction does not exists"}

        if referral_transaction.status == ReferralTransactions.Status.COMPLETED:
            logger.info("Transaction already completed")
            return { "status": "already_completed"}
        if referral_transaction.status == ReferralTransactions.Status.FAILED:
            logger.info("Transaction already failed")
            return { 'status': "already_failed"}
        if referral_transaction.status == ReferralTransactions.Status.REVERSED:
            logger.info("Transaction already reversed")
            return { "status": "already reversed"}
    
    paystack_service = PaystackService()

    create_transfer = paystack_service.initiate_transfer(
        amount=referral_transaction.amount, recipient_code=recipient_code, 
        reference=referral_transaction.reference_key,
        reason=f"Referral-WithDrawal {transaction_id}"
    )
    if not create_transfer['status']:
        logger.error("Paystack Error %s", create_transfer['message'])
        return {"status": False, "message": create_transfer['message']}

    data  = create_transfer['data']

    transfer_status = data['status']
    transfer_code = data['transfer_code']

    logger.info(
        "Paystack Response for transaction %s | transfer status: %s | transfer_code: %s", 
        transaction_id, transfer_status, transfer_code
    )
    with transaction.atomic():
        update_transaction = ReferralTransactions.objects\
            .filter(transaction_id=transaction_id)\
            .update(transfer_code=transfer_code)
        
    return {"status": True, "paystack_status": transfer_status}

@celery.shared_task(bind=True, max_retries=3, reject_on_worker_lost=True)
def process_transfer_task(self, transaction_id, recipient_code):
    try:
        process_transfer(transaction_id, recipient_code)
    except Exception as exc:
        logger.error("Referral transfer process task failed: %s", exc)
        raise self.retry(exc=exc, countdown=60 * 5) 
    

@celery.shared_task(bind=True, max_retries=3, reject_on_worker_lost=True)
def process_transfer_verification(self, webhook_response):
    logger.info("verify status | transfer status: %s", webhook_response['status'])

    if not isinstance(webhook_response, dict):
        logger.info("webhook even must be a valid dict obj")

    reference = webhook_response['reference']
    try:
        with transaction.atomic():
            try:
                transaction_instance = (
                    ReferralTransactions.objects.select_for_update(nowait=True)
                    .select_related("user").prefetch_related("referrals")
                    .get(reference_key=reference)
                )
            except ReferralTransactions.DoesNotExist:
                logger.info("transaction not found")
                return {"status": False, "message": "transaction_not_found"}
        
        if transaction_instance.status != ReferralTransactions.Status.PENDING:
            logger.info("Transaction is not pending")
            return { "status": False, "message": "transaction is not pending"}
        
        referrals = transaction_instance.referrals.all()

        for referral in referrals:
            if referral.status == Referral.Status.CONVERTED:
                logger.info("referral already moved: current status %s", referral.status)
                return { "status": False, "message": f"referral already moved to {referral.status}"}

        transfer_status = webhook_response['status']

        transaction_service = TransactionService()

        if transfer_status == "success":
            transaction_service.process_completed_transaction(transaction_instance)
        elif transfer_status == 'failed':
            transaction_service.process_failed_transaction(transaction_instance)
        elif transfer_status == 'reversed':
            transaction_service.process_reversed_transaction(transaction_instance)
        else:
            transaction_instance.save()
        transaction_instance.save()

        return { 'status': True, "message": "withdrawal  verified"}
    
    except Exception as exc:
        logger.error("Error verifying transaction :%s", exc)
        raise self.retry(exc=exc, countdown=60 * 5)







