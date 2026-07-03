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


def generate_thumbnails(url: str, start: int = 3, duration: int = 5, format: str = "webp"):
    """
    Generate thumbnails for a video from a given URL.
    """
    try:
        # transform the original url using 
        transform_str = f"so_{start},du_{duration},fl_animated/"
        anchor = "/video/upload/" # every cloudinary url carries this
        if anchor not in url:
            logger.debug("Invalid cloudinary structure")
            raise ValueError("Invalid Cloudinary structure")

        parts = url.split(anchor)
        modified_url = f"{parts[0]}{anchor}{transform_str}{parts[1]}"
        logger.info("Modified Str: "+ modified_url)

        change_format = modified_url.rsplit(".", 1)[0]
        base_url = f"{change_format}.{format}"

        logger.info("Final thumbnail_url: "+ base_url)
        return base_url
            
    except Exception as e:
        logger.error(f"Error generating thumbnail for {url}: {e}")
        return None