from faker import Faker

from django.contrib.auth import get_user_model

from apps.users.base_model import  BaseProfile
from apps.users.provider_models import ProviderModel, Service

import factory

UserModel = get_user_model()
faker_instance = Faker()

class CustomUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserModel

    email = faker_instance.email(safe=True)
    username = faker_instance.user_name()


class BaseProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BaseProfile
    
    user = factory.SubFactory(CustomUserFactory)
    display_name = factory.LazyAttribute(lambda obj: obj.user.username)

class ProviderProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProviderModel  
    
    profile = factory.SubFactory(BaseProfileFactory)

class ProviderServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Service

    profile = factory.SubFactory(ProviderProfileFactory)
    description = faker_instance.text(max_nb_chars=10)
    min_charge = 800
    max_charge = 1000
    
