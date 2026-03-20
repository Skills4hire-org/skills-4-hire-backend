import django_filters

from .customer_models import CustomerModel
from .provider_models import ProviderModel


class ProviderProfileFilter(django_filters.FilterSet):
    provider_name = django_filters.CharFilter(field_name="provider__display_name")
    title = django_filters.CharFilter(field_name="professional_title")
    experience_level = django_filters.CharFilter(field_name='experience_level')
    availability = django_filters.CharFilter(field_name='availability')
    min_charge = django_filters.NumberFilter(field_name='min_charge', lookup_expr='lte')
    max_charge = django_filters.NumberFilter(field_name='max_charge', lookup_expr="gte")
    hourly_pay = django_filters.NumberFilter(field_name="hourly_pay", lookup_expr="gte")

    year_of_experience = django_filters.NumberFilter(field_name="years_or_experience")
    open_to_full_time  = django_filters.BooleanFilter(field_name="open_to_full_time")

    is_top_rated = django_filters.BooleanFilter(field_name="is_top_rated")

    class Meta:
        model = ProviderModel
        fields = [
            "title", "experience_level",
            "availability", "min_charge",
            "max_charge", "hourly_pay",
            "year_of_experience", "open_to_full_time",
            "is_top_rated", "provider_name"
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