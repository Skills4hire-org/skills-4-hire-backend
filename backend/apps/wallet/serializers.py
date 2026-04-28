from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import Wallet, WalletTransaction, BankAccount
from .paystack.service import PaystackService, PaystackError
from .services import BankAccountService, WalletService
from ..referral.services.utils import generate_reference_key
from .transactions.services import WalletTransactionService
from .tasks import process_withdrawal_task


import uuid
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

class WalletDetailSerializer(serializers.ModelSerializer):
    available_balance = serializers.DecimalField(
        source="balance", read_only=True,
        max_digits=8, decimal_places=2)
    
    overall_balance = serializers.SerializerMethodField()

    overall_locked_balance = serializers.SerializerMethodField()
    
    user_email = serializers.CharField(source='user.email')

    class Meta:
        model = Wallet

        fields = [
            'wallet_id', 'user_email', 
            "is_active", 'created_at',
            'available_balance', 'overall_balance',
            'overall_locked_balance'
        ]

    def get_overall_balance(self, obj):
        return str(obj.get_total_balance)
    
    def get_overall_locked_balance(self, obj):
        return obj.locked_wallet
    
class DepositSerializer(serializers.ModelSerializer):

    class Meta:
        model = WalletTransaction
        fields = [
            "amount", "idempotency_key"
        ]

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("amount cannot be less than 0")
        
        return value
    
    def validate_idempotency_key(self, value):
        try:
            uuid.UUID(value)
        except Exception as e:
            raise serializers.ValidationError(f"Error validatind idempotency_key: {e}")
        return value
    

    def create(self, validated_data):
        user = self.context['request'].user

        try:
            user_wallet = Wallet.objects.get(user=user, is_active=True)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": "Wallet not found. Please contact support."}
            )
        
        reference_key = generate_reference_key(user)
        amount = validated_data['amount']
        idempotency_key =validated_data['idempotency_key']

        service = WalletTransactionService()

        transaction = service.create_wallet_transaction(
            amount=amount, user=user, wallet=user_wallet, 
            reference_key=reference_key, idempotency_key=idempotency_key,
            type=WalletTransaction.Type.DEPOSIT
        )

        if transaction['status']:
            validated_data['wallet_transaction'] = transaction['transaction']
        else:
            raise serializers.ValidationError(transaction['reason'])
        
        return validated_data

class WalletTransactionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            'transaction_id'
        ]

class RessolveBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = [
            "account_number", "bank_code",
            "bank_name"
        ]

    def validate_account_number(self, value: str) -> str:
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                "Account number must be exactly 10 digits."
            )
        return value

    def validate_bank_code(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("Bank code must be numeric.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user

        account_number = validated_data['account_number']
        bank_code = validated_data['bank_code']

        try:
            ressolve_service = PaystackService()
            response = ressolve_service.ressolve_bank(account_number, bank_code)
        except PaystackError as exc:
            logger.error(str(exc))
            raise serializers.ValidationError(f"Error: {str(exc)}")
        
        if response['status']:
            data = response['data']
            validated_data['account_name'] = data['account_name']
            validated_data['bank_id'] = data['bank_id']
            validated_data['user'] = user

            with transaction.atomic():
                super().create(validated_data=validated_data)
        else:
            raise serializers.ValidationError(response['message'])

        return validated_data

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = (
            "bank_account_id", "account_name",
            "account_number", "bank_code",
            "bank_name", "recipient_code",
            "bank_id", "is_active", 
            "created_at",
        )

class TransferRecepientSerializer(serializers.ModelSerializer):

    type = serializers.CharField(allow_blank=True, default="nuban", max_length=500, required=False)
    currency = serializers.CharField(allow_blank=True, default="NGN", max_length=50, required=False)

    class Meta:
        model = BankAccount
        fields = [
            "account_number", "bank_code",
            "account_name", "type", "currency"
        ]

    def validate_account_number(self, value: str) -> str:
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                "Account number must be exactly 10 digits."
            )
        return value

    def validate_bank_code(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("Bank code must be numeric.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user

        account_number = validated_data['account_number']
        bank_code = validated_data['bank_code']

        service = BankAccountService()
        bank_account = service.get_account_by_account_number(account_number)

        if not bank_account['status']:
            raise serializers.ValidationError(bank_account['message'])

        instance = bank_account['instance']

        if instance.user != user:
            raise PermissionDenied()
        
        if not instance.bank_code == bank_code:
            raise serializers.ValidationError("Bank code does not match")
        
        try:
            # create receipeint
            currency, type = validated_data['currency'], validated_data['type']

            paystack_service = PaystackService()
            create_receipient = paystack_service.create_transfer_recipient(
                account_name=instance.account_name, account_number=instance.account_number,
                bank_code=instance.bank_code, currency=currency, type=type
            )

        except PaystackError as exc:
            logger.error(str(exc))
            raise serializers.ValidationError(exc)
        
        if not create_receipient['status']:
                raise serializers.ValidationError(create_receipient['message'])
        data = create_receipient['data']

        instance.recipient_code = data['recipient_code']
        instance.bank_name = data['details']['bank_name']
        instance.save(update_fields=['recipient_code', "bank_name"])
        
        return instance

class WithDrawalSerializer(serializers.ModelSerializer):

    recipient_code = serializers.CharField(max_length=50, required=True, write_only=True)

    class Meta:
        model = WalletTransaction 
        fields = [
            "amount", "idempotency_key", 
            "recipient_code"
        ]

    def validate_recipient_code(self, value):
        user = self.context['request'].user
        exists = BankAccount.objects.filter(user=user, recipient_code=value, is_active=True).exists()

        if not exists:
            raise serializers.ValidationError("Invalid account number")

        return value
        
    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("amount cannot be negative")
        
        user = self.context['request'].user
        user_wallet = user.wallet if user.wallet else None

        if user_wallet is None:
            raise serializers.ValidationError("User wallet not found. transaction terminated")
        
        balance = user_wallet.balance

        if value > balance:
            raise serializers.ValidationError("Insufficient Funds")
        
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        recipient_code = validated_data.pop('recipient_code', None)
        
        reference_key = generate_reference_key(user)

        # process account deduction
        wallet_service = WalletService()
        try:

            validated_data.update({
                "reference_key": reference_key,
                "wallet": user.wallet,
                "user": user,
                "type": WalletTransaction.Type.WITHDRAW,
            })

            with transaction.atomic():
                wallet_service.deduct_user_balance(user, validated_data['amount'])
                transaction_instance = super().create(validated_data)
        
        except Exception as exc:
            raise serializers.ValidationError(exc)
        
        # process transfer transaction ( transaction_id, recipient_code)
        transaction_id = transaction_instance.pk
        process_withdrawal_task.delay(transaction_id, recipient_code)

        return transaction_instance





        