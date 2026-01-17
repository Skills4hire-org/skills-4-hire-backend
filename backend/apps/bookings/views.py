from rest_framework import viewsets, permissions

from .serializers import Bookings, BookingCreateSerialzer

class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = BookingCreateSerialzer
    queryset  = Bookings.objects.all()
