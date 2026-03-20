from django.db import transaction

from apps.core.utils.py import get_or_none
from ..models import UserAddress
from ...base_model import BaseProfile


class AddressService:

    @staticmethod
    def address_already_exists(user_profile, postal_code: str) -> bool:
        address = get_or_none(UserAddress, user_profile=user_profile, postal_code=postal_code)
        if address is None:
            return False
        return True

    @transaction.atomic
    def create_address(self, user_profile, validated_data):
        if "user_profile_id" in validated_data:
            validated_data.pop("user_profile_id")
        if not isinstance(user_profile, BaseProfile):
            raise ValueError("Invalid base profile instance")

        try:
            address = UserAddress.objects.create(
                user_profile=user_profile,
                **validated_data
            )
        except Exception as e:
            raise Exception(e)

        return address




