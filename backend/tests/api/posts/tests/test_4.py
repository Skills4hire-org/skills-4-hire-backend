import pytest
from .test_1 import  Post

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "post", "repost_quote"),
    [
        ("customer_client", "provider_post", "Quote"),
        ("provider_client", "customer_post", "Quote")
    ]
)
def test_repost(request, client, post, repost_quote):

    api_client = request.getfixturevalue(client)

    post = request.getfixturevalue(post)

    request_path = f'/api/v1/posts/{post.post_id}/repost/'

    request_data = {
        "repost_quote": repost_quote
    }

    response = api_client.post(
        path=request_path,
        data=request_data,
        format="json"
    )

    active_user = response.wsgi_request.user
    result = response.json()
    reposted_post = Post.objects.get(parent__pk=post.post_id)
    assert reposted_post.repost_quote == repost_quote
    assert  result["status"] == "success"
    assert reposted_post.reposted_by == active_user

