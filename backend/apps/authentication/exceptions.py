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

import functools
import logging


logger = logging.getLogger(__name__)

def retry_on_failure(retry):
    def hold_func(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            for _ in range(retry):
                logger.info("Starting Task execution...")
                if attempt >= retry:
                    logger.error("max attempts exceeded. try again later")
                    raise ValueError("max attempts exceeded. try again later") 
                response = func(*args, **kwargs)
                if response:
                    return response
                attempt += 1
                logger.info("Retrying request...")
        return wrapper
    return hold_func


                
