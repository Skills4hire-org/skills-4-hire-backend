"""
Utility functions used across the application.

Includes helpers for common operations like text sanitization, validation, etc.
"""

import re
import logging
from functools import wraps
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import escape, strip_tags
from django.conf import settings

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


def get_or_none(model, **kwargs):
    """
    Get a single object or return None if not found.

    Args:
        model: Django model class
        **kwargs: Query parameters

    Returns:
        Model instance or None
    """
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def log_action(action_type, user=None, details=None):
    """
    Log user actions for audit trail.

    Args:
        action_type (str): Type of action (e.g., 'message_sent', 'conversation_created')
        user (User): User performing the action
        details (dict): Additional action details
    """
    log_message = f"Action: {action_type}"

    if user:
        log_message += f" | User: {user.id}"

    if details:
        log_message += f" | Details: {details}"

    logger.info(log_message)


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


