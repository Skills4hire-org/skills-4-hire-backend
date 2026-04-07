from django.db import transaction

from ..models import WalletTransaction
from ..exceptions import DuplicateTransactionError

class WalletTransactionService:

    def create_wallet_transaction(self, amount, user, wallet, **validated_data):

        try:
            if WalletTransaction.objects.filter(idempotency_key=validated_data['idempotency_key']).first():
                raise DuplicateTransactionError()

            with transaction.atomic():
                wallet_transaction = WalletTransaction.objects.create(
                    amount=amount, user=user, wallet=wallet,
                    **validated_data
                )
        except DuplicateTransactionError as e:
            return {"status": False, "transaction": None}
        except Exception as e:
            return {"status": False, "transaction": None, 'reason': f"{str(e)}"}
        
        return {"status": True, "transaction": wallet_transaction}
    





