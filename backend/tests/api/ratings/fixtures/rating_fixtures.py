
import pytest

from ....factories.ratings import ReviewFactory, RatingFactory


@pytest.fixture
def review_fixture(db, customer, provider_profile):
    return ReviewFactory(reviewed_by=customer, provider_profile=provider_profile)

@pytest.fixture
def rate_fixture(db, customer, provider_profile):
    return RatingFactory(rate_by=customer, provider_profile=provider_profile)

