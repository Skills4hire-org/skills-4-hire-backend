from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import WalletTransaction
from .paystack.service import PaystackService
from .transactions.services import WalletTransactionService
from .services import WalletService

import uuid
import logging


MAX_RETRIES = 5
BASE_RETRY_DELAY = 60
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

@shared_task(bind=True, max_retries=3, default_retry_delay=300, autoretry_for=[Exception,], retry_backoff=True)
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


def process_withdrawal(transaction_id, recipient_code):

    logger.info(
        "Withdrawal processing Started for %s with code %s", 
        transaction_id, recipient_code)
    
    try:
        with transaction.atomic():
            try:
                withdrawal_transaction = (
                    WalletTransaction.objects.select_for_update(nowait=True)
                    .select_related("user", "wallet")
                    .get(transaction_id=transaction_id)
                )
            except WalletTransaction.DoesNotExist:
                logger.info("Transaction not found with transction id %s", transaction_id)
                return {"status": False, "message": "transction_not found"}

            transction_status = withdrawal_transaction.status

            if transction_status == WalletTransaction.Status.COMPLETED:
                logger.info("Transction with id %s alreary completed", transaction_id)
                return { "status": False, "message": "transction already completed"}
            
            if transction_status == WalletTransaction.Status.FAILED:
                logger.info("Transaction with id %s already failed", transaction_id)
                return { "status": False, "message": "transaction_alredy_failed"}
            
            withdrawal_transaction.status = WalletTransaction.Status.PROCESSING
            withdrawal_transaction.save(update_fields=['status', "updated_at"])

        paystack_service = PaystackService()

        amount = withdrawal_transaction.amount
        reference_key = withdrawal_transaction.reference_key

        transfer_response = paystack_service.initiate_transfer(
            amount=amount, reference=reference_key, recipient_code=recipient_code,
            reason="Withdrawal"
        )

        data = transfer_response['data']

        transfer_status = data['status']
        transfer_code = data['transfer_code']

        with transaction.atomic():
            withdrawal = (
                WalletTransaction.objects.select_for_update()
                .get(transaction_id=transaction_id)
            )

            withdrawal.transfer_code = transfer_code
            withdrawal.status = WalletTransaction.Status.PROCESSING

            withdrawal.save(update_fields=['transfer_code', 'updated_at', 'status'])
        
        return {"status": True, "message": "withdrawal processed"}
    
    except Exception as exc:
        raise

@shared_task(bind=True, max_retries=MAX_RETRIES, autoretry_for=(Exception, ), reject_on_worker_lost=True)
def process_withdrawal_task(self, transaction_id, recipient_code):
    try:
        process_withdrawal(transaction_id, recipient_code)
    except Exception as exc:

        if self.request.retries >= MAX_RETRIES:
            logger.info(
                "Retries reached limit, restoring user balance"
            )

            withdrawal = WalletTransaction.objects.get(transaction_id=transaction_id)
            transaction_service = WalletTransactionService()
            transaction_service.process_failed_withdrawal(withdrawal)


        return self.retry(exc=exc, countdown=60 * 3)
    

@shared_task(bind=True, max_retries=MAX_RETRIES, reject_on_worker_lost=True)
def process_withdrawal_verifications(self, webhook_data):
    
    logger.info(
        "processing withdrawal verifications: transaction status: %s", 
        webhook_data['status']
    )

    reference_key = webhook_data['reference']
    try:
        with transaction.atomic():
            try:

                withdrawal_transaction = (
                    WalletTransaction.objects.select_for_update(nowait=True)
                    .select_related("user", "wallet")
                    .get(reference_key=reference_key)
                )
            except WalletTransaction.DoesNotExist:
                logger.info("Transaction with reference key %s not found", reference_key)
                return { "status": False, "message": "Transaction not found"}

            transaction_status = withdrawal_transaction.status

            if transaction_status != WalletTransaction.Status.PROCESSING:
                logger.info("wallet transction is not processing. Current status: %s", transaction_status)
                return {"status": False, "message": "transaction is not processing. current "+ transaction_status}

            
            transfer_status = webhook_data['status']
            transaction_service = WalletTransactionService()

            if transfer_status in ('success', ):
                transaction_service.process_completed_withdrawal(withdrawal_transaction)
            elif transfer_status in ("failed", "reversed"):
                transaction_service.process_failed_withdrawal(withdrawal_transaction)
            
            else:
                withdrawal_transaction.status = WalletTransaction.Status.PROCESSING

            withdrawal_transaction.save(update_fields=['status', 'updated_at'])
        return {"status": True, "message": "transaction_processed"}
    
    except Exception as exc:

        logger.info("retrying tasks on exceptions: "+ str(exc))
        return self.retry(exc=exc, countdown=60 * 3)




            
