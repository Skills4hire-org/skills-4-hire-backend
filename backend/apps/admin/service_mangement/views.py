from rest_framework import viewsets

from .serializers import ServiceCategoryCreateSerializer
from ..permissions import IsAdmin

class ServiceCategoryManagementViewset(viewsets.ModelViewSet):
    serializer_class = ServiceCategoryCreateSerializer
    http_method_names = ["post", "delete", "patch", 'put']
    permission_classes = [IsAdmin]
    