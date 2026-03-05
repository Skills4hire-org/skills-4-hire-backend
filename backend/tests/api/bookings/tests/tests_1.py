from uuid import UUID
from faker import Faker
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q

from rest_framework import status

from apps.bookings.models import Bookings

import pytest

faker_instance = Faker()
cache.clear()

@pytest.mark.api
@pytest.mark.django_db
def test_customer_can_create_booking(
    customer_client, 
    customer_wallet, 
    provider_profile, 
    setup_bookings_create,
    provider_service,
    another_provider_service
):
    
    provider_id = provider_profile.pk
    assert isinstance(provider_id, UUID)

    request_data = setup_bookings_create

    request_path = f"/api/v1/{provider_id}/bookings/"

    response = customer_client.post(
        path=request_path, 
        data=request_data, 
        format="json"
    )
    result = response.json()
    assert result["status"] == 'success'
    assert response.status_code == 201

    # test customer can create booking with provider services

    request_data.update({
        "service": [
            {
                "name": "backend developer",
                "description": faker_instance.text(max_nb_chars=10),
                "min_charge": 600,
                "max_charge": 1000,
            },
            {
                "name": "fullstack developer",
                "min_charge": 600,
                "max_charge": 1000,
                "description": faker_instance.text(max_nb_chars=10)
            }
        ],
        "start_date": timezone.now(),
        "end_date": timezone.now() + timezone.timedelta(days=5)
    })

    service_response = customer_client.post(
        path=request_path, 
        data=request_data,
        format="json"
    )
    result = service_response.json()
    assert service_response.status_code == 201
    assert result["status"] == "success"
    assert len(result["detail"]["service"]) == 2
    for service in result["detail"]["service"]:
        assert service["name"] in ["backend developer".title(), "fullstack developer".title()]
    
@pytest.mark.api
@pytest.mark.django_db  
def test_provider_cannot_create_booking(
        provider_client,
        provider_profile,
        setup_bookings_create
):  

    provider_id = provider_profile.pk
    assert isinstance(provider_id, UUID)

    request_data = setup_bookings_create

    request_path = f"/api/v1/{provider_id}/bookings/"

    response = provider_client.post(
        path=request_path, 
        data=request_data, 
        format="json"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.api
@pytest.mark.django_db
def test_booking_update(
        customer_client,
        provider_profile,
        setup_bookings_create,
        booking_with_services,
        customer_wallet,
        provider_service,
        another_provider_service

):
    
    request_data = setup_bookings_create
    request_path = f"/api/v1/{provider_profile.pk}/bookings/{booking_with_services.pk}/"


    response = customer_client.put(
        path=request_path, 
        data=request_data,
        format="json")
    
    result = response.json()
    assert response.status_code == 200
    assert request_data["address"] is not None
    assert float(f"{request_data['price']:.2f}") == float(result["price"])
    assert booking_with_services.price != result["price"]

    
    # test with adding multiple provider services to booking
    request_data.update({
        "service": [
            {
                "name": "backend developer",
                "description": faker_instance.text(max_nb_chars=10),
                "min_charge": 600,
                "max_charge": 1000,
            },
            {
                "name": "fullstack developer",
                "min_charge": 600,
                "max_charge": 1000,
                "description": faker_instance.text(max_nb_chars=10)
            }
        ],
        "start_date": timezone.now(),
        "end_date": timezone.now() + timezone.timedelta(days=5)
    })


    response = customer_client.put(
                                path=request_path,
                                data=request_data,
                                format='json')
    
    assert response.status_code == 200
    assert request_data["address"] is not None
    assert float(f"{request_data['price']:.2f}") == float(result["price"])


@pytest.mark.api
@pytest.mark.django_db 
def test_wrong_booking_update(
        another_customer_client,
        provider_profile,
        setup_bookings_create,
        create_booking,
        customer_wallet,

):
    
    request_data = setup_bookings_create
    request_path = f"/api/v1/{provider_profile.pk}/bookings/{create_booking.pk}/"

    response = another_customer_client.put(
        path=request_path, 
        data=request_data,
        format="json")

    assert response.status_code == 403


@pytest.mark.api
@pytest.mark.django_db
def test_fetch_bookings_list_action(
    customer_client, 
    provider_profile,
    create_multiple_bookings
):
    request_path = f"/api/v1/{provider_profile.pk}/bookings/"
    response = customer_client.get(path=request_path)
    assert response.status_code == 200


@pytest.mark.api
@pytest.mark.django_db
def test_fetch_bookings_list_action(
    provider_client, 
    provider_profile,
    create_multiple_bookings
):
    request_path = f"/api/v1/{provider_profile.pk}/bookings/"
    response = provider_client.get(path=request_path)
    assert response.status_code == 200
    

@pytest.mark.api
@pytest.mark.django_db
def test_query_params(
        customer_client,
        provider_profile,
        create_multiple_bookings
):  
    
    booking_status = "COMPLETED"
    request_path = f"/api/v1/{provider_profile.pk}/bookings/"
    response = customer_client.get(request_path, {"status": booking_status})
    assert response.status_code == 200
    result = response.json()
    for data in result["results"]:
        assert booking_status == data["booking_status"]
    

@pytest.mark.api
@pytest.mark.django_db
def test_booking_provider(provider_client, create_multiple_bookings, provider_profile):
    request_path = "/api/v1/bookings/"
    response = provider_client.get(request_path)
    result = response.json()

    assert response.status_code == 200
    assert len(result["results"]) > 0
    for data in result["results"]:
        assert data["provider"]["provider_id"] == str(provider_profile.pk)
        

@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("api_client", "user_type"),
    [
        ("customer_client", "customer"),
        ("provider_client", "provider_profile")
    ]
)
def test_booking_fetch(
    request, api_client, user_type,
    create_multiple_bookings):

    client = request.getfixturevalue(api_client)
    active_user = request.getfixturevalue(user_type)
    request_path = "/api/v1/bookings/"
    response = client.get(request_path)
    result = response.json()

    assert response.status_code == 200
    assert len(result["results"]) > 0

    for data in result["results"]:
        if user_type == "customer":
            assert data['customer']["email"] == active_user.email


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("api_client", "user_type", "can_cancel"),
    [
        ("customer_client", "customer", True),
        ("provider_client", "provider_profile", True),
        ("another_customer_client", "another_customer", False)
    ]
)
def test_cancel_booking(
        request, api_client, user_type, 
        create_multiple_bookings, can_cancel):
    
    client = request.getfixturevalue(api_client)

    user = request.getfixturevalue(user_type)
    privider_pk = request.getfixturevalue("provider_profile").pk

    request_data = {
        "status": Bookings.BookingStatus.CANCELLED
    }
    if can_cancel:
        if user_type == "customer":
            booking = Bookings.objects.filter(customer=user, booking_status__icontains="pending").first()
        else:
            booking = Bookings.objects.filter(provider=user, booking_status__icontains="pending").first()
        request_path = f"/api/v1/{str(privider_pk)}/bookings/{booking.pk}/"

        response = client.patch(
            path=request_path, 
            data=request_data, 
            format="json")
    
        result = response.json()
        assert result["status"] == "success"
        assert response.status_code == 200
        
        update_booking = Bookings.objects.get(pk=booking.pk)
        assert update_booking.booking_status == Bookings.BookingStatus.CANCELLED
        if user_type == "customer":
            assert update_booking.cancelled_by == user
        else:
            assert update_booking.cancelled_by == user.profile.user
    else:
        customer = request.getfixturevalue("customer")
        booking = Bookings.objects.filter(
            customer=customer, 
            booking_status__icontains="pending").first()
        request_path = f"/api/v1/{str(privider_pk)}/bookings/{booking.pk}/"

        response = client.patch(
            path=request_path, 
            data=request_data, 
            format="json")
    
        assert response.status_code == 403


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("api_client", "user_type", "can_accept"),
    [
        ("provider_client", "provider_profile", True),
        ("customer_client", "customer", False)
    ]
)
def test_accept_booking(
    request, api_client, user_type, can_accept,
    create_multiple_bookings, customer_wallet):

    
    client = request.getfixturevalue(api_client)
    provider = request.getfixturevalue("provider_profile")

    booking = Bookings.objects.filter(
        customer=customer_wallet.user, 
        provider=provider, booking_status__icontains="pending").first()

    request_path = f"/api/v1/{provider.pk}/bookings/{booking.pk}/"

    request_data = {
        "status": Bookings.BookingStatus.COMPLETED
    }

    response = client.patch(path=request_path, data=request_data, format='json')
    if can_accept:
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"

        updated_booking = Bookings.objects.get(pk=booking.pk)
        if user_type == "provider_profile":
            assert updated_booking.accepted_by == provider.profile.user

    else:
        assert response.status_code == 403


@pytest.mark.api
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("api_client", "user_type", "can_delete"),
    [
        ("customer_client", "customer", True),
        ("provider_client", "provider_profile", False)
    ]
)
def test_booking_delete(
    request, api_client, user_type, can_delete,
    create_multiple_bookings,
):
    
    client = request.getfixturevalue(api_client)

    user = request.getfixturevalue(user_type)
    provider_pk = request.getfixturevalue("provider_profile").pk

    request_path = f"/api/v1/{provider_pk}/bookings/"

    if can_delete:
        if user_type == "customer":
            booking = Bookings.objects.filter(customer=user).first()
        else:
            booking = Bookings.objects.filter(provider=user).first()

        request_path += f"{booking.pk}/"

        response = client.delete(path=request_path)

        assert response.status_code == 204
        deleted_booking = Bookings.objects.get(pk=booking.pk)
        assert deleted_booking.is_active == False
        assert deleted_booking.is_deleted == True
    else:

        if user_type == "customer":
            booking = Bookings.objects.filter(customer=user).first()
        else:
            booking = Bookings.objects.filter(provider=user).first()

        request_path += f"{booking.pk}/"

        response = client.delete(path=request_path)
        assert response.status_code == 403
        deleted_booking = Bookings.objects.get(pk=booking.pk)
        assert deleted_booking.is_active == True
        assert deleted_booking.is_deleted == False

    

    


