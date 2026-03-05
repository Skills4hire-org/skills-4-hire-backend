from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import  get_user_model
from django.utils import  timezone

import logging
import  validators
import requests

from datetime import  datetime, timedelta
from ..models import Post, Category

logger = logging.getLogger(__name__)
UserModel = get_user_model()

def get_post_by_id(post_id):
    if post_id is None:
        return {"success": False, "msg": "POST_ID_NOT_PROVIDED"}
    
    try: 
        with transaction.atomic():
            post_instance = get_object_or_404(Post, pk=post_id, is_active=True, is_deleted=False)

    except Exception as exc :
        logger.exception(f"Error retrieving post with ID {post_id}")
        return {"success": False, "msg": f"POST_RETRIEVAL_FAILED: {str(exc)}"}
    
    return {"success": True, "post": post_instance}


def validate_url(url: str) -> tuple[bool, str]:
    if not validators.url(url):
        return False, "Not valid url"
    try:
        response = requests.head(url, timeout=5)
        if response.status_code == 200:
            return True, url
        return False, "Not Valid url"
    except requests.RequestException as e:
        return False, str(e)


def check_service_in_category(service_name: str):
    service_name_local = service_name.title()
    try:
        category = Category.objects.filter(name__iexact=service_name_local).first()
    except Category.DoesNotExist:
        return False, service_name_local
    return  True, category

def can_make_post(user_role: str, post_type: int) -> bool:
    allowed_services = {
        "users": [Post.PostType.GENERAL.value],
        "providers": [Post.PostType.GENERAL.value, Post.PostType.SERVICE.value],
        "customer": [Post.PostType.GENERAL.value, Post.PostType.JOB.value],
    }
    if user_role == UserModel.RoleChoices.SERVICE_PROVIDER:
        if post_type not in allowed_services["providers"]:
            return False
    elif user_role == UserModel.RoleChoices.CUSTOMER:
        if post_type not in allowed_services["customer"]:
            return  False
    elif user_role is None:
        if post_type not in allowed_services["users"]:
            return False

    return True

def verify_post_with_amount(amount: float, user_role: str, post_type: str) -> bool:
    if amount is not None:
        if user_role != UserModel.RoleChoices.CUSTOMER:
            return  False
        if post_type != Post.PostType.JOB.value:
            return  False
    elif not amount:
        if post_type == Post.PostType.JOB.value:
            return  False
    return True

def get_date(duration: int) -> tuple[datetime | None, datetime | None]:
    if duration:
        start_date = timezone.now()
        end_date = start_date + timedelta(days=duration)
        return start_date, end_date
    return None