from rest_framework import serializers

from .models import Wallet, WalletTransaction

import uuid
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
        from .helpers import reference
        from .transactions.services import WalletTransactionService

        user = self.context['request'].user

        try:
            user_wallet = Wallet.objects.get(user=user, is_active=True)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": "Wallet not found. Please contact support."}
            )
        
        reference_key = reference()
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

    
