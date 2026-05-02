from django.urls import path, include

from .views import BookingViewSet, BookingPaymentRequestViewSet

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register("bookings", BookingViewSet, basename='booking')
router.register('booking-payments', BookingPaymentRequestViewSet, basename='payout')

urlpatterns = [
    path('', include(router.urls)),
]