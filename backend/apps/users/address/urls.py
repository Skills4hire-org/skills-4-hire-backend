from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import AddressViewSet

address_router = DefaultRouter()

address_router.register("address", AddressViewSet, basename='address')

address_urlpatterns = [
    path("", include(address_router.urls))
]