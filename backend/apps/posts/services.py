
from .models import  Post, PostLike, Comment

from rest_framework.exceptions import PermissionDenied

from django.db import  transaction
from django.views.decorators.cache import cache_page
from datetime import  datetime

@transaction.atomic
def create_post(user, start_date: datetime | None, end_date: datetime | None, **kwargs):
    user_active_role =  getattr(user, "active_role")
    try:
        new_post = Post.objects.create(
            **kwargs,
            user=user, role=user_active_role,
            start_date=start_date, end_date=end_date
        )
    except Exception as e:
        raise Exception(e)
    return  new_post

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

    def list_nested_comments(self, comments, base_comments):
        qs = comments.filter(post=self.post, parent=base_comments).all().order_by("-created_at")
        if qs is None:
            return  self.list_comments(comments)
        return  qs



