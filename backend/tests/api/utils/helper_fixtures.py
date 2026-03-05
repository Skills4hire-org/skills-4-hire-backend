import pytest

from ...factories import ProviderServiceFactory

@pytest.fixture
def provider_service(db, provider_profile):
    name = "backend developer"
    return ProviderServiceFactory(
        profile=provider_profile,
        name=name.strip().title()
    )


@pytest.fixture
def another_provider_service(db, provider_profile):
    name = "fullstack developer"
    return ProviderServiceFactory(
        profile=provider_profile,
        name=name.strip().title()
    )