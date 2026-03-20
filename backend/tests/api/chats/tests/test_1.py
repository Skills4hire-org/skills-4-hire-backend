import random
import pytest
import faker

from  apps.chats.models import Message

faker_instance = faker.Faker()

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "user", "can_create", "other_user"),
    [
        ("customer_client", "customer", True, "provider"),
        ("provider_client", "provider", True, "customer"),
        ("customer_client", "customer", True, "another_customer"),
        ("customer_client", "customer", False, 'customer'),
        ("provider_client", "provider", False, "provider")
    ]
)
def test_create_conversation(request, client, user, can_create, other_user):

    api_client = request.getfixturevalue(client)

    parti_one = request.getfixturevalue(user)
    participant_two = request.getfixturevalue(other_user)
    request_path = '/api/v1/conversation/'

    request_data = {
        "participant_two_id": participant_two.pk,
    }
    response = api_client.post(
        request_path,
        data=request_data,
        format="json",
    )

    result = response.json()

    if can_create:
        assert response.status_code == 201
        assert  "conversation_id" in result

        parpnt_one = result["participant_one"]
        assert parpnt_one["email"] == parti_one.email

        parpnt_two = result['participant_two']
        assert parpnt_two["email"] == participant_two.email
    else:
        assert response.status_code == 400


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "user", "conversation"),
    [
        ("customer_client", "customer", "conversation_fixture"),
        ("provider_client", "provider", "conversation_fixture")
    ]
)
def test_list_conversation(request, client, user, conversation):

    conversation = request.getfixturevalue(conversation)

    api_client = request.getfixturevalue(client)
    user_profiles = request.getfixturevalue(user)

    request_path = '/api/v1/conversation/'

    response = api_client.get(request_path)
    result = response.json()

    assert  response.status_code == 200

    if user == "customer":
        assert user_profiles.email == conversation.participant_one.email
    else:
        assert  user_profiles.email == conversation.participant_two.email

    assert "pagination" in result


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "user", "can_view", "conversation"),
    [
        ("customer_client", "customer", True, "conversation_fixture"),
        ("provider_client", "provider", True, "conversation_fixture"),
        ("another_customer_client", "another_customer", False, "conversation_fixture")
    ]
)
def test_single_conversation(request, client, user, can_view, conversation):

    conversation_obj = request.getfixturevalue(conversation)
    api_client = request.getfixturevalue(client)

    user_obj = request.getfixturevalue(user)

    request_path  = f'/api/v1/conversation/{conversation_obj.pk}/'

    response = api_client.get(request_path)
    result = response.json()
    participants = (conversation_obj.participant_one, conversation_obj.participant_two)
    if can_view:
        assert response.status_code == 200

        assert user_obj in participants
        assert  "messages" and "conversation_id" in result

    else:
        assert  user_obj not in participants
        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "user", "message", "can_send", "conversation"),
    [
        ("customer_client", "customer", "Hello skilled professional", True, "conversation_fixture"),
        ("provider_client", "provider", "Hello my able customer", True, "conversation_fixture"),
        ("another_customer_client", "another_customer", "hello from another customer", False, "conversation_fixture")

    ]
)
def test_send_message(request, client, user, message, can_send, conversation):

    api_client = request.getfixturevalue(client)
    conversation_obj = request.getfixturevalue(conversation)
    user_obj = request.getfixturevalue(user)

    request_path = f"/api/v1/conversation/{conversation_obj.pk}/messages/"

    request_data  = {
        "content": message
    }

    response = api_client.post(
        path=request_path,
        data=request_data,
        format="json",
    )
    if can_send:
        assert response.status_code == 201
    else:
        assert response.status_code == 403


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client", "conversation"),
    [
        ("customer_client", "conversation_fixture")
    ]
)
def test_negotiations(request, client, conversation):

    api_client = request.getfixturevalue(client)

    conversation_obj = request.getfixturevalue(conversation)

    request_path = '/api/v1/negotiation/'
    request_data = {
        "price": 3000.00,
        "conversation_id": conversation_obj.pk
    }
    response = api_client.post(
        request_path,
        data=request_data,
        format='json'
    )

    result = response.json()
    assert response.status_code == 201
    assert  "sender" in result and "conversation_id" in result
