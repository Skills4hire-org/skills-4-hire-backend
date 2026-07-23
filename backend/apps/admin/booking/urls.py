from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import BookingAdminViewsets

router = DefaultRouter()

router.register("bookings", BookingAdminViewsets, basename='admin-booking-view')

urlpatterns = [
    path("", include(router.urls))
]