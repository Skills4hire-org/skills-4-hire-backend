from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views


booking_list = views.BookingViewSet.as_view({
    "post": "create",
    "get": "list"
})
booking_detail = views.BookingViewSet.as_view({
    "put": "update",
    "patch": "patial_update",
    "get": "retrieve",
    "delete": "destroy"
})

urlpatterns = [
    path("profile/<uuid:profile_pk>/bookings/", booking_list, name="booking-list"),
    path("profile/<uuid:profile_pk>/bookings/<uuid:booking_pk>/", booking_detail, name="booking-detail")
]