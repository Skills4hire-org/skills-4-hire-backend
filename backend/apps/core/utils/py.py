import logging

logger = logging.getLogger(__name__)

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