from rest_framework.test import APIClient as Client
import pytest

@pytest.mark.api
@pytest.mark.django_db
class TestAuth:
    
    def test_registration(self, base_client: Client):
        request_path = "/api/v1/auth/register/"

        response = base_client.post(path=request_path)
        print(response.json())

        