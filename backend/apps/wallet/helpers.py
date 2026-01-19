from .models import Wallet

from django.db import transaction, DatabaseError
from django.contrib.auth import get_user_model

from rest_framework.exceptions import ValidationError

User = get_user_model()

def _save_wallet_on_account_creation(user):
    if not isinstance(user, User):
        raise ValidationError("'user' is not a valid 'CustomUser' instance")
    try:
        with transaction.atomic():
            wallet = Wallet.objects.create(user=user)
            return True
    except DatabaseError:
        raise
    except Exception:
        raise
