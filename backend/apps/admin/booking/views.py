from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend

from ..pagination import AdminPagination
from ..permissions import IsAdmin
from .serializers import AdminBookingListSerializer, Bookings

class BookingAdminViewsets(viewsets.ModelViewSet):
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    pagination_class = AdminPagination
    serializer_class = AdminBookingListSerializer
    permission_classes = [IsAdmin]
    filterset_fields = {
        'created_at': ['exact', 'gte', 'lte', 'date'],
    }

    def get_queryset(self):
        queryset = Bookings.objects.select_related("customer", 'provider')
        return self.filter_queryset(queryset)



