import pytest
import random

from . import service_post
from .setup import  Post

from tests.factories import  PostFactory, PostLikeFactory, CommentFactory

@pytest.fixture
def customer_post(db, customer):
    return  PostFactory(
        user=customer
    )

@pytest.fixture
def provider_post(db, provider):
    return  PostFactory(
        user=provider
    )

@pytest.fixture
def create_multiple_posts(db, provider, customer):
    posts = []
    users = [provider, customer]
    for i in range(5):
        general_post = PostFactory(
            user=random.choice(users),
            post_type=Post.PostType.GENERAL.value,
            post_content="general_posts"
        )

        posts.append(general_post)
    for i in range(5):
        job_post = PostFactory(
            user=customer,
            post_type=Post.PostType.JOB.value,
            post_content="job_posts"
        )
        posts.append(job_post)
    for i in range(5):
        service_post = PostFactory(
            user=provider,
            post_type=Post.PostType.SERVICE.value,
            post_content="service_posts"
        )
        posts.append(service_post)

    return  posts

@pytest.fixture
def create_like(db, customer_post, provider):
    like = PostLikeFactory(
        post=customer_post,
        user=provider
    )
    return like


@pytest.fixture
def create_10_comments_customer(db, another_customer, provider, customer_post):
    # add  comments on customer post

    users = [another_customer, provider]
    comments = []
    for i in range(11):
        customer_comments = CommentFactory(
            user=random.choice(users),
            post=customer_post,
        )
        comments.append(customer_comments)

    return  comments

@pytest.fixture
def create_10_comments_provider(db, another_customer, customer, provider_post):
    users = [another_customer, customer]
    comments = []
    for i in range(11):
        customer_comments = CommentFactory(
            user=random.choice(users),
            post=provider_post,
        )
        comments.append(customer_comments)

    return  comments

@pytest.fixture
def add_comment_customer(db, customer, provider_post):
    return  CommentFactory(
        user=customer,
        post=provider_post
    )

@pytest.fixture
def add_comment_provider(db, provider, customer_post):
    return  CommentFactory(
        user=provider,
        post=customer_post
    )


