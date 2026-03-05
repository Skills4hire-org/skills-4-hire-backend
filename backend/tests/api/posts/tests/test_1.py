import pytest
from  ..fixtures.setup import valid_post_content

from apps.posts.models import  Post

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "user_type", "can_post", "post_type"),
    [
        ("customer_client", "customer", True, "general_post"),
        ("provider_client", "provider", True, "general_post"),
        ("customer_client", "customer", True, "job_post"),
        ("customer_client", "customer", False, "service_post"),
        ("provider_client", "provider", True, "service_post"),
        ("provider_client", "provider", False, "job_post"),
    ]
)
def test_create_post(setup_post_create, request, client, user_type, can_post, post_type):

    request_path = "/api/v1/posts/"
    post_type = request.getfixturevalue(post_type)

    data: dict = setup_post_create

    request_data: dict = valid_post_content(data, post_type)

    api_client = request.getfixturevalue(client)

    response = api_client.post(
        request_path,
        data=request_data,
        format="json",
    )

    result = response.json()
    if not can_post:
        assert  response.status_code == 403

    else:
        assert  response.status_code == 201
        assert  result["detail"]["post_content"] == request_data["post_content"]


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "can_update", "post_owner", "post", "post_type"),
    [
        ("customer_client", True, "customer", "customer_post", "general_post"),
        ("provider_client",  True, "provider", "provider_post", "service_post"),
        ("customer_client", False, "provider", "provider_post", "general_post"),
        ("provider_client", False, "customer", "customer_post", "job_post")
    ]
)
def test_update_post(
        setup_post_create, request,
        client, can_update, post_owner,
        post, post_type,):

    api_client = request.getfixturevalue(client)
    post = request.getfixturevalue(post)
    post_type = request.getfixturevalue(post_type)
    request_path = f"/api/v1/posts/{post.post_id}/"

    data = setup_post_create
    request_data = valid_post_content(data, post_type)

    request_data.pop("attachment")

    response = api_client.put(
        path=request_path,
        data=request_data,
        format='json'
    )
    result = response.json()
    if not can_update:
        assert  response.status_code == 403
    else :
        assert  response.status_code == 200
        assert result["post_content"] == request_data["post_content"]


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "user_type"),
    [
        ("customer_client", "customer"),
        ("provider_client", "provider")
    ]
)
def test_list_post(create_multiple_posts, request, client, user_type):

    api_client = request.getfixturevalue(client)

    request_path = "/api/v1/posts/"

    response = api_client.get(
        path=request_path
    )
    result = response.json()
    total_posts = len(result['results'])
    assert  total_posts == 15
    assert response.status_code == 200
    # ensure pagination in response
    assert  "next" and "previous" in result

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "user_type"),
    [
        ("customer_client", "customer"),
        ("provider_client", "provider")
    ]
)
def test_user_posts(create_multiple_posts, request, client, user_type):

    api_client = request.getfixturevalue(client)
    user = request.getfixturevalue(user_type)
    request_path = "/api/v1/posts/mine/"

    response = api_client.get(
        path=request_path
    )

    result = response.json()
    assert  response.status_code == 200
    posts = result["results"]
    for post in posts:
        if user_type == "customer":
            assert post["user"]["email"] == user.email
        elif user_type == "provider":
            assert  post["user"]["email"] == user.email
        else :
            assert post["user"]["email"] == user.email
    assert "next" and "previous" in result


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "user"),
    [
        ("customer_client", "customer"),
        ("provider_client", "provider")
    ]
)
def test_offers_posts(
        create_multiple_posts, request,
        client, user
):

    api_client = request.getfixturevalue(client)

    request_path = "/api/v1/posts/offers/"
    response = api_client.get(
        path=request_path
    )

    result: dict = response.json()
    if user == "customer":
        assert response.status_code == 200
        posts = result["results"]
        assert len(posts) == 5
        for post in posts:
            assert post["post_type"] == Post.PostType.JOB.value

    else:
        assert  response.status_code == 403

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "post_owner", "can_delete"),
    [
        ("customer_client", "customer_post", True),
        ("provider_client", "customer_post", False),
        ("provider_client", "provider_post", True),
        ("customer_client", "provider_post", False)

    ]
)
def test_delete_post(request, client, post_owner, can_delete):

    post = request.getfixturevalue(post_owner)
    api_client = request.getfixturevalue(client)
    assert post.is_active == True
    assert  post.is_deleted == False
    request_path = f"/api/v1/posts/{post.post_id}/"

    response = api_client.delete(
        path=request_path
    )
    if not can_delete:
        assert  response.status_code == 403
    else:
        assert response.status_code == 204

        deleted_post = Post.objects.get(post_id=post.post_id)
        assert deleted_post.is_active == False
        assert  deleted_post.is_deleted == True
