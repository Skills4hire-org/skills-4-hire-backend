import pytest

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def base_client(db):
    """
    Base API client fixture for testing.
     - Provides an instance of APIClient for making HTTP requests in tests.
     - UnAuthenticated by default
    """
    return APIClient()


@pytest.fixture
def customer_client(db, base_client, customer):
    token = RefreshToken.for_user(user=customer)
    base_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
    )
    return base_client


@pytest.fixture
def provider_client(db, base_client, provider):
    token = RefreshToken.for_user(user=provider)
    base_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
    )
    return base_client

@pytest.fixture
def another_customer_client(db, base_client, another_customer):
    token = RefreshToken.for_user(user=another_customer)
    base_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
    )
    return base_client
