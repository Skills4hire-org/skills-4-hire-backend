from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import WalletTransaction
from .paystack.service import PaystackService
from .services import WalletService

import uuid
import logging


MAX_RETRIES = 5
BASE_RETRY_DELAY = 60  # seconds
logger = logging.getLogger(__name__)

def process_deposit(wallet_transaction_id: uuid.UUID) -> dict:

    logger.info(f"Task process: \nProcessing Deposit {wallet_transaction_id}")

    try:
        with transaction.atomic():
            try:
                wallet_transaction = WalletTransaction.is_active_objects\
                                .select_for_update(nowait=True)\
                                .select_related("user", 'wallet')\
                                .get(pk=wallet_transaction_id)
            except WalletTransaction.DoesNotExist:
                logger.error("wallet transaction not found")
                return {'status': False, "reason": "Wallet Transaction not found"}
    
            if wallet_transaction.status == WalletTransaction.Status.COMPLETED:
                logger.info("Wallet transaction alreary completed")
                return {"status": True, "reason": 'already completed'}
            
            if wallet_transaction == WalletTransaction.Status.FAILED:
                logger.info("wallet transaction already failed")
                return {"status": False, "reason": "already Failed"}


            wallet_transaction.status = WalletTransaction.Status.PROCESSING
            wallet_transaction.save(update_fields=['status', 'updated_at'])
        
        # Process Paystack payment Initialization

        paystack_service = PaystackService()

        initialize_payment = paystack_service.initialize_deposit(
            wallet_transaction.amount, user=wallet_transaction.user, 
            reference=wallet_transaction.reference_key
        ) 

        return initialize_payment

    except Exception as exc:
        logger.exception(
            "Unexpected error processing withdrawal %s: %s", wallet_transaction.pk, exc
        )

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    autoretry_for=[Exception,],
    retry_backoff=True
)
def verify_deposit_status(self, webhook_data: dict):
    logger.info("Task Execution: Processing Task, Deposit verifications")

    payment_status = webhook_data.get("status")
    payment_reference = webhook_data.get("reference")

    try:
        w_transaction = WalletTransaction.objects\
                    .select_for_update(nowait=True)\
                    .select_related("user", "wallet")\
                    .get(reference_key=payment_reference)
        
    except WalletTransaction.DoesNotExist:
        logger.info("No transaction found for this payment")
        return {'status': "payment_not_found"}
    
    if w_transaction.status == WalletTransaction.Status.COMPLETED:
        logger.info("this transaction already completed")
        return {"status": "payment_already_completed"}

    if w_transaction.status == WalletTransaction.Status.FAILED:
        logger.info("This transaction already failed")
        return {"status": "transaction_already_failed"}

    if payment_status == "success":
        try:
            service = PaystackService()
            verify_transaction = service.verify_deposit(payment_reference)
        except Exception as exc:
            logger.exception("Error verifying payment")
            # self.request.retry(exc=exc)
            return 

        status = verify_transaction['data']['status']

        with transaction.atomic():
            w_transaction = WalletTransaction.objects\
                            .select_for_update(nowait=True)\
                            .get(reference_key=payment_reference)

            if status == "success":
                user = w_transaction.user
                amount_naira = verify_transaction['data']['amount'] / 100
                
                wallet = WalletService().credit_user_wallet(user, amount_naira)

                w_transaction.status = WalletTransaction.Status.COMPLETED
                w_transaction.completed_at = timezone.now()

            elif status.lower() in ("failed", "reversed"):
                w_transaction.failed_at = timezone.now()
                w_transaction.status = WalletTransaction.Status.FAILED

            meta_data = verify_transaction['data']['authorization']
            customer = verify_transaction['data']['customer']
            meta_data.update(customer)
            w_transaction.metadata = meta_data

            w_transaction.save()
    else:
        w_transaction.status = WalletTransaction.Status.FAILED
        w_transaction.failed_at = timezone.now()

        w_transaction.save()
    return "Deposit veified"



    













