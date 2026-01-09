from rest_framework.serializers import Serializer
from django.core.exceptions import ValidationError
import logging


logger = logging.getLogger(__name__)

class BaseService:
    def __init__(self, serializer: Serializer):
        if not isinstance(serializer, Serializer):
            logger.warn(f" {serializer} is not a Serializer object")
            raise ValidationError("Invalid Serializer objecccct provided")

        self.serializer = serializer

    def _validate_serializer(self):

        return self.serializer.is_valid(raise_exception=True)
