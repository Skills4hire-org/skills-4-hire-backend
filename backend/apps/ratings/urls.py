from django.urls import path, include


from rest_framework.routers import DefaultRouter

from apps.ratings.views import ReviewViewSet, RatingViewSet

routers = DefaultRouter()

routers.register('ratings', RatingViewSet, basename="rating")
routers.register("reviews", ReviewViewSet, basename='review')

urlpatterns = [
    path("", include(routers.urls))
]

