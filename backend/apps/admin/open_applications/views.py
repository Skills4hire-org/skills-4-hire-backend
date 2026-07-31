from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import ApplicationCategorySerializer, ApplicationCreateSerializer
from .models import ApplicationCategory, OpenApplications
from ..permissions import IsAdmin
from ..pagination import AdminPagination

class ApplicationCategoryViewset(viewsets.ModelViewSet):
    serializer_class = ApplicationCategorySerializer
    queryset = ApplicationCategory.objects.all()
    permission_classes = [IsAdmin]
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['name']
    ordering_fields = ['name']
    ordering = ['-name']


class OpenApplicationViewset(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    pagination_class = AdminPagination
    queryset = OpenApplications.objects.select_related("category")
    serializer_class = ApplicationCreateSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "title": ['icontains', 'iexact'],
        "description": ["icontains"],
        "location": ['icontains']
    }
    ordering_fields = ['-created_at']
    ordering = ['-created_at']