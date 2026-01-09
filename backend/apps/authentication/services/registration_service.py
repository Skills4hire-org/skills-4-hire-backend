import logging
from apps.authentication.exceptions import SerializerNotValidException
from django.db import transaction
from apps.authentication.services.baase_service import BaseService


logging.basicConfig(level=logging.INFO)

class RegistrationsService(BaseService):
    """  
    A class for handling any related registrations services
    
    Accept  Validated data and perform registration operations

    """

    @transaction.atomic()
    def register_service(self):
        """ 
        """
        try:
            if not self._validate_serializer():
                raise SerializerNotValidException

            # save user data if serializer is valid
            self.serializer.save()

        except Exception as exc:
            logging.error(f"error occurred: {exc}")
            raise exc
        
        return self.serializer.validated_data
