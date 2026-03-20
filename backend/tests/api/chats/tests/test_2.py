import pytest
import random
import faker

from apps.chats.models import Negotiations

from backend.tests.api.chats.fixtures import conversation_fixture

faker_instance = faker.Faker()

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "negotiation", "status", "will_pass", "track"),
    [
        ("customer_client", "can_negotiate_fixture", "accept", True, 1),
        ("provider_client", "can_negotiate_fixture", "accept", True, 2),
        ("customer_client", "can_negotiate_fixture", "reject", True, 3),
        ("provider_client", "can_negotiate_fixture", "reject", True, 4),
        ("customer_client", "can_negotiate_fixture", 'counter', True,5),
        ("provider_client", "can_negotiate_fixture", 'counter', True, 6),
        ("customer_client", "cannot_negotiate_fixture", "accept", False, 7),
        ("provider_client", "cannot_negotiate_fixture", "reject", False, 8),
        ("customer_client", "cannot_negotiate_fixture", "counter", False, 9),
        ("another_customer_client", "can_negotiate_fixture", "counter", False, 10),

    ]
)
def test_negotiation_update(request, client, negotiation, status, will_pass, track):
    api_client = request.getfixturevalue(client)

    negotiation_obj = request.getfixturevalue(negotiation)

    request_path = f"/api/v1/negotiation/{negotiation_obj.pk}/{status}/"

    match status:
        case "accept":
            status_data = "ACCEPTED"
        case "reject":
            status_data = "REJECTED"
        case "counter":
            status_data = "COUNTERED"
        case _:
            status_data = "UNKNOWN"

    request_data = {
        "price": random.randint(100, 5000),
        "note": faker_instance.text(max_nb_chars=10),
        "status": status_data
    }
    response = api_client.post(
        path=request_path,
        data=request_data,
        format='json'
    )

    result = response.json()
    print("Test_track:", track)
    user = response.wsgi_request.user
    if not will_pass:
        assert response.status_code in (400, 403)
    else:
        assert response.status_code == 200
        updated_negotiation = Negotiations.objects.get(pk=negotiation_obj.pk)
        if status == "accepted":
            assert updated_negotiation.final_price is not None and \
                   updated_negotiation.final_price == request_data["price"]

        assert updated_negotiation.sender == user


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "can_view", "conversation"),
    [
        ('customer_client', True, "conversation_fixture"),
        ("another_customer_client", False, "conversation_fixture")
    ]
)
def test_list_messages(request, client, can_view, conversation):

    api_client = request.getfixturevalue(client)
    conversation_obj = request.getfixturevalue(conversation)

    request_path = f"api/v1/conversation/{conversation_obj.pk}/messages/"
    response = api_client.get(path=request_path)

    result = response.json()
    print(result)






