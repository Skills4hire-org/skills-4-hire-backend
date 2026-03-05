import pytest

from  apps.posts.models import Comment
from apps.notification.models import Notification


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "post", "message"),
    [
        ("customer_client", "customer_post", "Customer_comment"),
        ("provider_client", "customer_post", "Hello Customer"),
        ("provider_client", "provider_post", "Hello"),
        ("customer_client", "provider_post", "hello Provider")
    ]
)
def test_add_comment(request, client, post, message):

    api_client = request.getfixturevalue(client)
    post = request.getfixturevalue(post)

    request_data = {
        "message": message
    }
    request_path = f"/api/v1/posts/{post.post_id}/comment/"

    response = api_client.post(
        path=request_path,
        data=request_data,
        format="json"
    )
    result = response.json()
    assert  response.status_code == 201

    assert result["status"] == "success"

    comment = Comment.objects.get(post=post)
    current_user = response.wsgi_request.user

    assert  current_user == comment.user
    assert  comment.message == message
    assert  Notification.objects.get(sender=current_user, receiver=post.user)

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "post", "comments"),
    [
        ("customer_client", "customer_post", "create_10_comments_customer"),
        ("provider_client", "provider_post", "create_10_comments_provider"),
    ]
)
def test_list_comments(
        request, client, post, comments
):
    api_client = request.getfixturevalue(client)
    post = request.getfixturevalue(post)

    comments_all = request.getfixturevalue(comments)
    request_path = f"/api/v1/posts/{post.post_id}/comment/"

    response = api_client.get(
        path=request_path
    )

    result = response.json()

    assert  response.status_code == 200

    comments_result: dict = result["results"]
    for comment in comments_result:
        assert comment["comment_counts"] == len(comments_all)
        assert  comment["post"] == str(post.post_id)


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ('client', "user", "comments", "can_update", "message"),
    [
        ("customer_client", "customer", "add_comment_customer", True, "update_message"),
        ("provider_client", "provider", "add_comment_provider", True, "update_message"),
        ("provider_client", "provider", "add_comment_customer", False, "update_message"),
        ("customer_client", "customer", "add_comment_provider", False, "update_message"),
    ]
)
def test_update_comment(request, client, user, comments, can_update, message):

    comment = request.getfixturevalue(comments)

    api_client = request.getfixturevalue(client)
    request_path = f'/api/v1/posts/{comment.post.post_id}/comment/{comment.pk}/'
    request_data = {
        "message": message
    }

    response = api_client.put(
        path=request_path,
        data=request_data,
        format='json'
    )
    result = response.json()
    if not can_update:
        assert  response.status_code == 403
    else:
        assert response.status_code == 200
        assert  result["message"] == message


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ('client', "user", "comments", "can_delete"),
    [
        ("customer_client", "customer", "add_comment_customer", True),
        ("provider_client", "provider", "add_comment_provider", True),
        ("provider_client", "provider", "add_comment_customer", False),
        ("customer_client", "customer", "add_comment_provider", False),
    ]
)
def test_delete_comment(request, client, user, comments, can_delete):

    api_client = request.getfixturevalue(client)
    comment = request.getfixturevalue(comments)

    request_path = f'/api/v1/posts/{comment.post.pk}/comment/{comment.pk}/'

    response = api_client.delete(
        path=request_path,
    )

    if not can_delete:
        assert  response.status_code == 403
    else:
        assert  response.status_code == 204
        deleted_comment = Comment.objects.get(pk=comment.pk)
        assert  deleted_comment.is_deleted == True
        assert  deleted_comment.is_active == False

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "user", "comment", "message"),
    [
        ("customer_client", "customer", "add_comment_customer", "nested_comment"),
    ]
)
def test_nested_comment(request, client, user, comment, message):

    api_client = request.getfixturevalue(client)

    comment = request.getfixturevalue(comment)

    request_path = f"/api/v1/posts/{comment.post.pk}/comment/{comment.pk}/comments/"
    request_data = {
        "message": message
    }

    response = api_client.post(
        path=request_path,
        data=request_data,
        format='json'
    )
    result = response.json()
    nested_comment = Comment.objects.get(parent=comment)
    assert  nested_comment.message == message
    assert result["status"] == ["success"]

