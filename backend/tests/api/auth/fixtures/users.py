from ....factories import (
    CustomUserFactory, 
    UserModel,
    ProviderProfileFactory
)

import pytest

@pytest.fixture
def user(db):
    return CustomUserFactory(
        email="nonverifieduser@gmail.com"
    )

@pytest.fixture
def verified_user(db, user):
    user.email = "verifieduser@gmail.com",
    user.is_active = True
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def provider(db, user):
    user = CustomUserFactory()
    user.email = "provideremail@gmail.com"
    user.is_active = True
    user.is_verified = True
    user.is_provider = True
    user.active_role = UserModel.RoleChoices.SERVICE_PROVIDER
    user.save()
    return user

@pytest.fixture
def customer(db):
    user = CustomUserFactory()
    user.email = "customeremail@gmail.com"
    user.is_active = True
    user.is_verified = True
    user.is_customer = True
    user.active_role = UserModel.RoleChoices.CUSTOMER
    user.save()
    return user

@pytest.fixture
def another_customer(db):
    user = CustomUserFactory()
    user.email = "anothercustomer@gmail.com"
    user.is_active = True
    user.is_verified = True
    user.is_provider = True
    user.is_customer = True
    user.active_role = UserModel.RoleChoices.CUSTOMER
    user.save()
    return user

@pytest.fixture
def customer_base_profile(db, customer):
    return customer.profile

@pytest.fixture
def provider_base_profile(db, provider):
    return provider.profile

@pytest.fixture
def provider_profile(db, provider_base_profile):
    return ProviderProfileFactory(profile=provider_base_profile)

@pytest.fixture
def customer_wallet(db, customer):
    wallet = customer.wallet
    wallet.balance = 10000
    wallet.save()
    return wallet
    