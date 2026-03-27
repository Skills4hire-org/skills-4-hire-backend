import uuid

from .models import  Post, PostLike, Comment

from rest_framework.exceptions import PermissionDenied, NotFound

from django.db import  transaction
from django.contrib.auth import  get_user_model
from datetime import  datetime


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

def list_nested_reposts(post, queryset):
    qs = queryset.filter(parent=post).all()
    if qs is None:
        return  None
    return  qs

def get_post_by_id(post_pk: uuid.UUID):
    try:
        post = Post.objects.get(post_id=post_pk)
    except Post.DoesNotExist:
        raise NotFound("post not found", code=404)
    return post


def get_offers_or_job_post(user: UserModel | None, queryset, include_offers: bool = True):
    if queryset is None:
        return None
    if include_offers:
        if user is not None:
           qs = queryset\
                .filter(user=user, post_type=Post.PostType.JOB.value)\
                .order_by("-created_at")
        else:
            qs = queryset.filter(post_type=Post.PostType.JOB.value)
        return qs
    else:
        if user is not None:
            qs = queryset\
                .filter(user=user)\
                .order_by("-created_at")

            return qs
        return None

def return_paginated_view(self, queryset):
    page = self.paginate_queryset(queryset)
    if page is not  None:
        serializer = self.get_serializer(page, many=True)
        return  self.get_paginated_response(serializer.data)
    serializer = self.get_serializer(queryset, many=True)
    return  serializer.data

class LikeService:
    def __init__(self, post, user):
        self.post = post
        self.user = user

    def check_already_liked_post(self):
        liked_post = PostLike.is_active_objects.filter(user=self.user, post=self.post).exists()
        if liked_post:
            return  True
        else:
            return False

    @transaction.atomic
    def create_like_post(self, **kwargs):
        if self.check_already_liked_post():
            raise PermissionDenied("You already liked this post")
        try:
            new_like = PostLike.objects.create(user=self.user, post=self.post, **kwargs)
        except Exception as e:
            raise Exception(e)
        return  new_like

    @transaction.atomic
    def unlike_post(self):
        if not self.check_already_liked_post():
            raise PermissionDenied("No like instance on this post")
        try:
            liked_post = PostLike.is_active_objects.get(user=self.user, post=self.post)
        except PostLike.DoesNotExist:
            raise Exception(f"{self.post} does not exist")

        liked_post.soft_delete()
        return liked_post

class CommentService:
    def __init__(self, post, user)->None:
        self.post = post
        self.user = user

    @transaction.atomic
    def add_comment(self, **kwargs):
        try:
            new_comment = Comment.objects.create(
                post=self.post,
                user=self.user,
                **kwargs
            )
        except Exception as e:
            raise Exception(e)
        return  new_comment


    def list_comments(self, comments):
        """ List comment service ( list comment associated to the current post )"""
        qs = comments.filter(post=self.post).all().order_by("-created_at")
        return  qs

    def create_nested_replies(self, **kwargs):
        return  self.add_comment(**kwargs)



