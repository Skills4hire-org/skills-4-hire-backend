import uuid

from .models import  Post, Likes, Comment

from rest_framework.exceptions import PermissionDenied, NotFound

from django.db import  transaction
from django.contrib.auth import  get_user_model
from datetime import  datetime
from django.db.models import Q


UserModel = get_user_model()

@transaction.atomic
def create_post(user, start_date: datetime | None = None, end_date: datetime | None = None, **kwargs):
    try:
        new_post = Post.objects.create(
            **kwargs,
            user=user,
            start_date=start_date, end_date=end_date
        )
    except Exception as e:
        raise Exception(e)
    return  new_post

def get_post_by_id(post_pk: uuid.UUID):
    try:
        post = Post.objects.get(post_id=post_pk)
    except Post.DoesNotExist:
        raise NotFound("post not found", code=404)
    return post


def get_offers_or_job_post(user,  queryset, include_offers):
    if queryset is None:
        return None
    if include_offers:
        if user is not None:
           qs = queryset\
                .filter(user=user, post_type=Post.PostType.JOB)\
                .order_by("-created_at", "-updated_at")
        else:
            qs = queryset.filter(post_type=Post.PostType.JOB.value)
        return qs

def list_posts(user, queryset):
    return queryset.filter(user=user).order_by("-created_at", "-updated_at")


def return_paginated_view(self, queryset):
    page = self.paginate_queryset(queryset)
    if page is not  None:
        serializer = self.get_serializer(page, many=True)
        return  self.get_paginated_response(serializer.data)
    serializer = self.get_serializer(queryset, many=True)
    return  serializer.data

class LikeService:
    def __init__(self):
        pass 

    def check_already_liked_post(self, user, post) -> bool:
        return Likes.is_active_objects.filter(user=user, post=post).exists()
    
    def check_already_liked_comment(self, user, comment):
        return Likes.is_active_objects.filter(user=user, comment=comment).exists()

    
    def like_comment(self, comment, user):
        if self.check_already_liked_comment(user, comment):
            raise PermissionDenied("You already liked this comment")
        like = Likes.objects.create(user=user, comment=comment)
        return like
    
    def unlike_comment(self, comment, user):
        if not self.check_already_liked_comment(user, comment):
            raise PermissionDenied("NO like instance found")
        
        try:
            like = Likes.is_active_objects.get(user=user, comment=comment)
        except Likes.DoesNotExist:
            raise ValueError("this object does not exists")

        like.soft_delete()
        return True

    @transaction.atomic
    def create_like_post(self, post, user, **kwargs):
        if self.check_already_liked_post(user, post):
            raise PermissionDenied("You already liked this post")
        try:
            new_like = Likes.objects.create(user=user, post=post)
        except Exception as e:
            raise Exception(e)
        return  new_like

    @transaction.atomic
    def unlike_post(self, post, user):
        if not self.check_already_liked_post(user, post):
            raise PermissionDenied("No like instance on this post")
        try:
            liked_post = Likes.is_active_objects.get(user=user, post=post)
        except Likes.DoesNotExist:
            raise Exception(f"post does not exist")

        if liked_post.user != user:
            raise PermissionDenied()
        
        liked_post.soft_delete()
        return liked_post

class CommentService:
    def __init__(self):
        pass

    @transaction.atomic
    def add_comment(self, post=None, parent=None, user=None, message=None):
        if user is None:
            raise Exception("A valid user object is required to create a comment.")
        
        if post is None and parent is not None:
            post = parent.post

        try:
            new_comment = Comment.objects.create(
                post=post,
                parent=parent,
                user=user,
                message=message
            )
            return new_comment
        except Exception as e:
            raise e

    def list_comments(self, comments):
        """ List comment service ( list comment associated to the current post )"""
        qs = comments.filter(post=self.post).all().order_by("-created_at")
        return  qs



