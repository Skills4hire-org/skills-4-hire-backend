
import pytest
import faker

from apps.ratings.models import ProfileRating, ProfileReview


faker_instance  = faker.Faker()

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "profile", "action", "can_add"),
    [
        ("customer_client", "provider_profile", "reviews", True),
        ("customer_client", "provider_profile", "ratings", True),
        ("provider_client", "provider_profile", "ratings", False),
    ]
)
def test_rating_review(request, client, profile, action, can_add):

    api_client = request.getfixturevalue(client)
    provider_profile = request.getfixturevalue(profile)
    request_path = f'/api/v1/{action}/'

    request_data = {
        "provider_profile_id": provider_profile.pk,
    }
    if action == "ratings":
        request_data.update({"rating": 4})
    elif action == "reviews":
        request_data.update({"review": faker_instance.text(max_nb_chars=20)})

    response = api_client.post(
        path=request_path,
        data=request_data,
        format='json'
    )

    result = response.json()
    current_user = response.wsgi_request.user

    if can_add:
        assert "rating_id" in result or "review_id" in result
        if action == "ratings":
            assert result["rate_by"] == current_user.email
        else:
            assert result["reviewed_by"] == current_user.email
    else:
        assert response.status_code == 403


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "action", "queryset"),
    [
       ("customer_client", "ratings", "rate_fixture"),
       ("provider_client", "reviews", "review_fixture"),
       ("customer_client", "reviews", "review_fixture"),
       ("provider_client", "ratings", "rate_fixture")
    ]
)
def test_rating_review_list(request, client, action, queryset):
    api_client = request.getfixturevalue(client)

    value = request.getfixturevalue(queryset)

    request_path = f"/api/v1/{action}/"
    response = api_client.get(path=request_path)

    result = response.json()
    assert response.status_code == 200

    assert "next" and "previous" in result['pagination']


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "obj", "action", "perform", "will_pass"),
    [
        ("provider_client", "rate_fixture", "get", "ratings", True),
        ("provider_client", "review_fixture", "get", "reviews", True),
        ("customer_client", "rate_fixture", "update", "ratings", True),
        ("customer_client", "review_fixture", "update", "reviews", True),
        ("provider_client", "review_fixture", "update", "reviews", False),
        ("customer_client", "rate_fixture", "delete", "ratings", True),
        ("customer_client", "review_fixture", "delete", "reviews", True),
        ("provider_client", "review_fixture", "delete", "reviews", False)

    ]
)
def test_obj_modify(request, client, obj, action, perform, will_pass):
    request_data = None
    api_client = request.getfixturevalue(client)

    obj = request.getfixturevalue(obj)
    request_path = f"/api/v1/{perform}/{obj.pk}/"
    if action == "get":
        response = api_client.get(path=request_path)

    elif action == "update":
        if perform == "ratings":
            request_data = {"rating": 3, "provider_profile_id": obj.provider_profile.pk}
        else:
            request_data = {"review": faker_instance.text(max_nb_chars=20),"provider_profile_id": obj.provider_profile.pk}
        response = api_client.patch(path=request_path, data=request_data, format="json")
    else:
        response = api_client.delete(path=request_path)

    result = response.json()

    if action == "delete":
        if not will_pass:
            assert response.status_code == 403
        else:
            assert  response.status_code == 204
        if perform == "ratings":
            deleted_rating = ProfileRating.objects.get(pk=obj.pk)
            assert deleted_rating.is_active == False
        else:
            pass
            # deleted_review = ProfileReview.objects.get(pk=obj.pk)
            # assert deleted_review.is_active == False

    if action  == "update":
        if not will_pass:
            assert response.status_code == 403

        if perform == "reviews":
            pass
            # updated_review = ProfileReview.objects.get(pk=obj.pk)
            # assert updated_review.review == request_data["review"]

        else:
            updated_rating = ProfileRating.objects.get(pk=obj.pk)
            assert updated_rating.rating == request_data["rating"]

        assert response.status_code == 200

    if action == "get":
        assert response.status_code == 200




