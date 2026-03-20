import factory

from .users import CustomUserFactory, faker_instance
from .users import ProviderProfileFactory
from apps.ratings.models import ProfileReview, ProfileRating


class RatingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProfileRating

    rate_by = factory.SubFactory(CustomUserFactory)
    provider_profile = factory.SubFactory(ProviderProfileFactory)
    rating = 5

class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProfileReview

    reviewed_by = factory.SubFactory(CustomUserFactory)
    provider_profile = factory.SubFactory(ProviderProfileFactory)
    review = faker_instance.text(max_nb_chars=200)



