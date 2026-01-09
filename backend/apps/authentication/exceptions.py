from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _

class SerializerNotValidException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Error occurred while validating serializer. Check passed data")
    default_code = "error"


class ServiceAlreadyExpired(ValueError):
    """ Raise when a service request is expired"""
    pass