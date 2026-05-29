import django_filters

from .customer_models import CustomerModel
from .provider_models import ProviderModel


class ProviderProfileFilter(django_filters.FilterSet):
    provider_name = django_filters.CharFilter(field_name="provider__display_name")
    title = django_filters.CharFilter(field_name="professional_title")
    experience_level = django_filters.CharFilter(field_name='experience_level')
    availability = django_filters.CharFilter(field_name='availability')
    class Meta:
        model = ProviderModel
        fields = [
            "title", "experience_level",
            "availability", "provider_name"
        ]


class CustomerProfileFilter(django_filters.FilterSet):
    customer_name = django_filters.CharFilter(field_name="profile__display_name")
    city = django_filters.CharFilter(field_name="city")
    industry = django_filters.CharFilter(field_name="industry_name")
    is_verified = django_filters.BooleanFilter(field_name="is_verified")


    class Meta:
        model = CustomerModel
        fields = [
            "customer_name", "city",
            "industry", "is_verified"
        ]