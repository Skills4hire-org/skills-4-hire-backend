from django.db import transaction

from ..base_model import BaseProfile
from ..customer_models import CustomerModel


class CustomerService:

    @transaction.atomic
    def create_customer(self, user_base_profile, validated_data: dict | None = None):

        if not isinstance(user_base_profile, BaseProfile):
            raise ValueError("not a valid base profile")

        try:
            if validated_data is not None:
                customer_profile = CustomerModel.objects.get_or_create(profile=user_base_profile, **validated_data)
            else:
                customer_profile = CustomerModel.objects.get_or_create(profile=user_base_profile)
            setattr(user_base_profile.user, "is_customer", True)
            user_base_profile.user.save(update_fields=["is_customer"])
        except Exception as e:
            raise ValueError(str(e))
        return customer_profile

