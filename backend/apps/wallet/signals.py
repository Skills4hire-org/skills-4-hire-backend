from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import LockedWallet


@receiver(signal=post_save, sender=LockedWallet)
def create_transaction_on_booking_lock(sender, instance, created, **kwargs):
    if not created:
        return
    if not isinstance(instance, LockedWallet):
        return

    # create transaction

