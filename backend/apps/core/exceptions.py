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
    return Response(
        {
            "success": False,
            "message": message,
            "errors": errors,
            "status_code": status_code,
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
    if response is not None:
        status_code = response.status_code
        data = response.data
        errors = data

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
            message = detail if isinstance(detail, str) else str(detail)
            errors = data
        else:
            message = data.get("detail", "An error occurred") if isinstance(data, dict) else str(data)
            errors = data

        return Response(
            {
                "success": False,
                "message": message,
                "errors": errors,
                "status_code": status_code,
            },
            status=status_code,
        )

    # Fallback when DRF cannot handle the exception
    return Response(
        {
            "success": False,
            "message": "Internal server error",
            "errors": {"detail": str(exc)},
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
