from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
import logging
import traceback

logger = logging.getLogger(__name__)


def api_response(data=None, message="Operation successful", status_code=status.HTTP_200_OK):
    if data is None:
        data = {}
    return Response(
        {
            "success": True,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def error_response(message="Validation failed", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    if errors is None:
        errors = {}
    
    formatted_message = ""
    if isinstance(errors, dict):
        for key, value in errors.items():
            if isinstance(value, (list, tuple)):
                formatted_message += f"{key}: {', '.join(map(str, value))} "
            else:
                formatted_message += f"{key}: {value} "
    elif isinstance(errors, (list, tuple)):
        formatted_message = ", ".join(map(str, errors))
    else:
        formatted_message = str(errors)

    return Response(
        {
            "success": False,
            "message": formatted_message.strip(),
            "errors": errors,
            "status_code": status_code,
            'extra_message': message
        },
        status=status_code,
    )


class BusinessLogicError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A business logic error occurred."
    default_code = "business_logic_error"

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        super().__init__(detail=detail, code=code)


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    # If DRF could not handle the exception it's an internal server error.
    if response is None:
        # Log full exception details server-side for review (including traceback)
        logger.error("Unhandled exception in request: %s", exc)
        # Build a sanitized 500 response without exposing internal details
        response = Response(
            {
                "success": False,
                "errors": {},
                "message": "An internal server error occurred.",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "data": {},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    status_code = response.status_code
    data = response.data
    errors = data

    # Parse appropriate messages
    if isinstance(exc, ValidationError):
        message = "Validation failed"
    elif isinstance(exc, (NotFound,)):
        message = data.get("detail", "Not found")
        errors = {"detail": data.get("detail", "Not found")}
    elif isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
        message = data.get("detail", "Permission denied")
        errors = {"detail": data.get("detail", "Permission denied")}
    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        message = data.get("detail", "Authentication failed")
        errors = {"detail": data.get("detail", "Authentication failed")}
    elif isinstance(exc, APIException):
        detail = data.get("detail", data)
        # Keep the API exception detail but avoid sending internal tracebacks.
        message = detail if isinstance(detail, str) else str(detail)
        errors = data
    else:
        # Non-DRF exceptions that reached here are unexpected; log and sanitize.
        logger.error("Unexpected exception handled: %s", exc)
        message = data.get("detail", "An error occurred") if isinstance(data, dict) else "An error occurred"
        errors = {} if status_code >= 500 else data

    # Build the string representation for message
    error_response_str = ""
    if isinstance(errors, dict):
        for key, value in errors.items():
            if isinstance(value, list):
                error_response_str += f"{key}: {', '.join(map(str, value))}: "
            else: 
                error_response_str += f"{key}: {value} "
    elif isinstance(errors, list):
        error_response_str = ", ".join(map(str, errors))
    else:
        error_response_str = str(errors)

    # For server errors do not expose internal error strings to the client.
    if status_code >= 500:
        client_message = "An internal server error occurred."
        client_errors = {}
    else:
        client_message = error_response_str.strip() or (message if isinstance(message, str) else "")
        client_errors = errors

    response.data = {
        "success": False,
        "message": client_message,
        "status_code": status_code,
        "errors": client_errors,
        "extra_message": message if status_code < 500 else "Server error",
    }

    return response
