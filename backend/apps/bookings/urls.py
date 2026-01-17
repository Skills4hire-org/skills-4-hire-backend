from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views

routers = DefaultRouter()

routers.register(f"bookings", views.BookingViewSet, basename="bookings")

urlpatterns = [
    path("", include(routers.urls))
]