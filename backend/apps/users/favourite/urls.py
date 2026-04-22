from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import FavouriteViewSet

router = DefaultRouter()

router.register("favourite", FavouriteViewSet, basename="favourite")

favourite_urlpatterns = [
    path("", include(router.urls))
]

