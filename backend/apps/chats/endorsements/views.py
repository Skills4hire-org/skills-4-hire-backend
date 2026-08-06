from rest_framework import viewsets, permissions
from .serializers import (
    EndorsementCreateSerializer, EndorsementDetailSerializer
)
from .models import Endorsements
from ...core.exceptions import api_response
from .permissions import IsEndorsementCreateUser, IsEndorsementOwner
from .paginations import EndorsementPagination

from django.shortcuts import get_object_or_404

class EndorsementViewset(viewsets.ModelViewSet):
    pagination_class = EndorsementPagination
    
    def perform_create(self, serializer):
        serializer.save(endorsed_by=self.request.user)

    def get_queryset(self):
        queryset =  queryset = Endorsements.objects.select_related("provider", "endorsed_by")
        query_params: bool = self.request.query_params.get("mine")
        other = self.request.query_params.get("other")
        if query_params:
            queryset = queryset.filter(provider=self.request.user.profile.provider_profile)
        if other:
            queryset = queryset.filter(provider__pk=other)
        else:
            queryset = queryset.filter(endorsed_by=self.request.user)

        return queryset

    def get_object(self):
        return super().get_object()

    def retrieve(self, request, *args, **kwargs):
        lookup_field = kwargs.get("pk")
        instance = get_object_or_404(Endorsements, pk=lookup_field)
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance)
        return api_response(data=serializer.data)

    def get_permissions(self):
        if self.action in ('update', "partial_update", "create"):
            return [IsEndorsementCreateUser()]
        elif self.action == "destroy":
            return [IsEndorsementOwner()]
        else:
            return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return EndorsementCreateSerializer
        else:
            return EndorsementDetailSerializer
        