from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views


booking_list = views.BookingViewSet.as_view({
    "post": "create",
    "get": "list",
})

booking_detail = views.BookingViewSet.as_view({
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
    "get": "retrieve"
})


booking_fetch = views.BookingViewSet.as_view({
    "get": "fetch_bookings"
})


urlpatterns = [
    path("bookings/", booking_fetch, name="booking-fetch"),
    path("<uuid:profile_pk>/bookings/", booking_list, name="booking-list"),
    path("<uuid:profile_pk>/bookings/<uuid:pk>/", booking_detail, name="booking-detail"),
]
