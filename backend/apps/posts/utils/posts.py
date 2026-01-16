from django.shortcuts import get_object_or_404
from django.db import transaction

import logging

from ..models import Post

logger = logging.getLogger(__name__)

def get_post_by_id(post_id):
    if post_id is None:
        return {"success": False, "msg": "POST_ID_NOT_PROVIDED"}
    
    try: 
        with transaction.atomic():
            post_instnce = get_object_or_404(Post, pk=post_id, is_active=True, is_deleted=False)

    except Exception as exc :
        logger.exception(f"Error retrieving post with ID {post_id}")
        return {"success": False, "msg": f"POST_RETRIEVAL_FAILED: {str(exc)}"}
    
    return {"success": True, "post": post_instnce}