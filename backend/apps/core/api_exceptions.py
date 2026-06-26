from rest_framework import status
from rest_framework.exceptions import APIException


class BusinessLogicError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A business logic error occurred."
    default_code = "business_logic_error"
