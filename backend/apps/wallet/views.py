from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .serializers import WalletDetailSerializer, DepositSerializer,\
      WalletTransactionDetailSerializer
from .models import Wallet, WalletTransaction, WebhookEvent
from .tasks import process_deposit, verify_deposit_status
from .paystack.service import PaystackService

from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

import logging, json

logger = logging.getLogger(__name__)

class WalletViewSet(viewsets.GenericViewSet):

    serializer_class = WalletDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        try:
            user_wallet = Wallet.objects.filter(is_active=True, user=self.request.user) \
                .select_related("user")\
                .prefetch_related("locked_balance")\
                .first()
        except Wallet.DoesNotExist:
            raise ValidationError("User wallet not found!")
        
        except Exception as e:
            raise ValidationError(f"Failed to fetch user wallet: {e}")
        

        return user_wallet

    @action(methods=['get'], detail=False, url_path="wallet")
    def wallet(self, request, *args, **kwargs):

        u_wallet = self.get_queryset()
        serialize_wallet = self.get_serializer(u_wallet)
        return Response(serialize_wallet.data, status=status.HTTP_200_OK)
    

class WalletTransactionViewSet(viewsets.GenericViewSet):

    http_method_names = ['post']

    def get_permissions(self):
        if self.action == 'webhook':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'deposit':
            return DepositSerializer
        return None

    @action(methods=['post'], detail=False, url_path="deposit")
    def deposit(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        idempotency_key = validated_data['idempotency_key']

        existing_transaction = WalletTransaction.objects.filter(
            user=request.user, idempotency_key=idempotency_key
        ).first()

        if existing_transaction:
            logger.info("Duplicate Transaction found for this request")
            return Response({
                "status":"failed",
                'message': "Duplicated transaction, returning existing transaction",
                'data': WalletTransactionDetailSerializer(existing_transaction).data
            }, status=status.HTTP_400_BAD_REQUEST)

        saved_data  = serializer.save()

        if "wallet_transaction" not in saved_data:
            logger.info("failed to fetch transaction")
            return Response({
                "status": "failed",
                'message': "failed to fetch transaction",
            }, status=status.HTTP_400_BAD_REQUEST
            )
        
        wallet_transaction = saved_data['wallet_transaction']
        if wallet_transaction:
            process_transction = process_deposit(wallet_transaction.pk)
        
        logger.info("Deposit initialized %s", wallet_transaction.pk)

        return Response(
            {
                "status": "success",
                "message": "Deposit initiated successfully.",
                "data":  process_transction,
            },
            status=status.HTTP_201_CREATED,
        )


    @action(methods=["POST"], detail=False, url_path="paystack-webhook")
    def webhook(self, request, *args, **kwargs):

        EVENT_HANDLERS = {
            "charge.success": verify_deposit_status
        }
        service = PaystackService()

        if not service._verify_signature(request):
            logger.info("Invalid signature for payment")
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError as exc:
            logger.warning(f"Paystack Webhoonk: Failed {str(exc)}")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        event = payload.get("event", "")
        data = payload.get("data")
        payment_reference = data.get("reference") or data.get("transfer_code")


        if payment_reference is None:
            logger.info("Paystack Webhook has no event, %s", event)
            return Response(status=status.HTTP_200_OK)
        
        webhook_event, created = WebhookEvent.objects.get_or_create(
                reference=payment_reference, 
                defaults={
                    "event_type": event,
                    "status": WebhookEvent.Status.RECEIVED,
                    "payload": payload
                }
            )

        if not created:
                logger.info("Webhook Found for this event %s", event)
                return Response(status=status.HTTP_200_OK, data={'msg': "Duplicate webhook found"})

        try:
            webhook_event.status = WebhookEvent.Status.PROCESSING
            webhook_event.save(update_fields=['status'])

            handler = EVENT_HANDLERS.get(event)
            if handler is None:

                logger.info("Paystack webhook: no handler for event type '%s'", event)

                webhook_event.status = WebhookEvent.Status.PROCESSED
                webhook_event.processed_at = timezone.now()
                webhook_event.save(update_fields=["status", "processed_at"])
                return Response(status=200)
            
            handler.delay(data)
            webhook_event.status       = WebhookEvent.Status.PROCESSED
            webhook_event.processed_at = timezone.now()
            webhook_event.save(update_fields=["status", "processed_at"])

        except Exception as exc:
            logger.exception("Paystack webhook: handler failed for %s (%s)", event, payment_reference)

            webhook_event.status = WebhookEvent.Status.FAILED
            webhook_event.error  = str(exc)
            webhook_event.save(update_fields=["status", "error"])
    
        return Response(status=200)









