import  pytest

from apps.posts.models import PostLike
from apps.notification.models import Notification

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ('client', "post", "user"),
    [
        ("customer_client", "customer_post", "customer"),
        ("customer_client", "provider_post", "provider"),
        ("provider_client", "customer_post", "customer"),
        ("provider_client", "provider_post", "provider"),
    ]
)
def test_like_post(request, post, client, user):
    api_client = request.getfixturevalue(client)
    post_instance = request.getfixturevalue(post)


    request_path = f"/api/v1/posts/{post_instance.post_id}/like/"

    response = api_client.post(
        path=request_path
    )
    assert  response.status_code == 201

    result = response.json()
    assert  result["status"] == "success"

    like = PostLike.is_active_objects.get(post__pk=post_instance.post_id)

    assert  like.post == post_instance

    assert  Notification.objects.filter(sender=like.user, receiver=like.post.user).first()


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ('client', "post", "user"),
    [
        ("provider_client", "customer_post", "customer"),
    ]
)
def test_double_like_same_post(request, client, post, user):

    api_client = request.getfixturevalue(client)
    post_instance = request.getfixturevalue(post)


    request_path = f'/api/v1/posts/{post_instance.post_id}/like/'

    for i in range(1, 3):
        response = api_client.post(
            path=request_path
        )
        if i > 1:
            assert response.status_code == 400
        else:
            assert response.status_code == 201



@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "post"),
    [
        ("provider_client", "customer_post")
    ]
)
def test_unlike_post(request, client, post, create_like):

    api_client = request.getfixturevalue(client)
    post_instance = request.getfixturevalue(post)

    request_path = f'/api/v1/posts/{post_instance.post_id}/unlike/'

    response = api_client.delete(
        path=request_path
    )
    assert  response.status_code == 200
    result = response.json()
    assert  result["status"] == ['success']

    like = PostLike.objects.get(postlike_id=create_like.pk)
    assert like.is_active == False
