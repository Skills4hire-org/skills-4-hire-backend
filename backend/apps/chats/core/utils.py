"""
Utility functions used across the application.

Includes helpers for common operations like text sanitization, validation, etc.
"""

import re
import logging
from functools import wraps
from decimal import Decimal

from django.utils.html import escape
from rest_framework.exceptions import ValidationError

from  ..services.conversations import NegotiationHistoryService, Negotiations
from ...notification.services import send_general_notification
from ...notification.events import NotificationEvents
logger = logging.getLogger(__name__)


def sanitize_message_content(content):
    """
    Sanitize message content to prevent XSS attacks.

    Args:
        content (str): Raw message content from user

    Returns:
        str: Sanitized message content
    """
    if not isinstance(content, str):
        return ''

    # Remove leading/trailing whitespace
    content = content.strip()

    # Escape HTML special characters
    content = escape(content)

    # Remove multiple consecutive spaces (but keep single spaces)
    content = re.sub(r' +', ' ', content)

    return content


def validate_message_content(content):
    """
    Validate message content.

    Args:
        content (str): Message content to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not content or not isinstance(content, str):
        return False, 'Message content is required'

    content = content.strip()

    if len(content) == 0:
        return False, 'Message cannot be empty'

    if len(content) > 5000:
        return False, 'Message exceeds maximum length of 5000 characters'

    return True, None

def validate_negotiation_notes(notes):
    if notes and not isinstance(notes, str):
        return  False, "No a valid str instance"

    if notes and len(notes) < 5:
        return False, "Provide a detailed characters 5 min"
    if len(notes) > 1000:
        return  False, "max length exceeded, 1000 chars"

    return  True, notes.strip()


def validate_negotiation_price(price):
    if not price or not isinstance(price, Decimal):
        return  False, "price is required and must be a valid float instance"
    return  True, price

def validate_status(status):
    if status is None:
        return  False, "status cannot be empty when negotiating"
    if status not in Negotiations.Status.values:
        return  False, "invalid field 'status'"
    return  True, status.strip()


def log_history(negotiation, sender, price, action):
    history = NegotiationHistoryService(
        negotiation=negotiation,
        sender=sender,
        price=price,
        action=action
    )
    create_history = history.create_history()
    return  create_history


def paginate_queryset(queryset, request, paginator):
    """
    Helper function to paginate a queryset.

    Args:
        queryset: Django QuerySet to paginate
        request: HTTP request object
        paginator: DRF pagination class instance

    Returns:
        tuple: (paginated_data, paginated_response)
    """
    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        return page, paginator.get_paginated_response
    return queryset, None



def timeit(func):
    """
    Decorator to measure function execution time.

    Usage:
        @timeit
        def my_function():
            pass
    """
    import time

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time
        logger.debug(f"{func.__name__} took {execution_time:.4f} seconds")

        return result

    return wrapper


def get_client_ip(request):
    """
    Get client IP address from request.

    Handles proxy headers (X-Forwarded-For, X-Real-IP).

    Args:
        request: HTTP request object

    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def format_timestamp(timestamp):
    """
    Format timestamp for API responses.

    Args:
        timestamp: datetime object

    Returns:
        str: Formatted ISO timestamp
    """
    if timestamp:
        return timestamp.isoformat()
    return None

def truncate_text(text, length=100):
    """
    Truncate text to specified length with ellipsis.

    Args:
        text (str): Text to truncate
        length (int): Maximum length

    Returns:
        str: Truncated text
    """
    if len(text) > length:
        return text[:length] + '...'
    return text

def trigger_notification(notification_type, sender, receiver):

    types = Negotiations.Status.values
    if notification_type not in types:
        raise ValidationError("type in valid")

    message = ""
    match notification_type:
        case Negotiations.Status.PROPOSED.value:
            message = f"{sender.full_name} Proposed an Offer"
        case Negotiations.Status.COUNTERED.value:
            message = f"{sender.full_name} countered your offer"
        case Negotiations.Status.ACCEPTED.value:
            message = f"{sender.full_name} accepted your offer"
        case Negotiations.Status.REJECTED.value:
            message = f'{sender.full_name} rejected your offer'
        case _:
            message = None

    event = NotificationEvents.MESSAGE.value
    try:
        send_general_notification(
            sender=sender,
            receiver=receiver,
            message=message,
            event=event
        )
    except Exception as e:
        logger.exception(f"Error sending notification: {e}")
