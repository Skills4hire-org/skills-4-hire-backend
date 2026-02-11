
from .serializers import ServiceSerializer, Service
from ...bookings.paginations import CustomBookingPagination

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response


class ServiceViewSet(ListCreateAPIView):
    serializer_class = ServiceSerializer
    queryset = Service.objects.select_related("profile").prefetch_related("images")
    permission_classes = [permissions.IsAuthenticated]

    pagination_class = CustomBookingPagination

    def get_queryset(self):
        user_profile = getattr(self.request.user.profile, "provider_profile", None)
        if user_profile is None:
            return None
        qs = self.queryset.filter(
            profile=user_profile, 
            is_active=True, is_deleted=False)
        if not qs.exists():
            return qs.none()
        return qs

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        profile_pk = kwargs.get("profile_pk")
        user_profile = getattr(request.user, "profile")
        if user_profile.pk != profile_pk:
            raise PermissionDenied()
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(data={"detail": "Service created successfully", "status": "success", "data": serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)
    
    @method_decorator(cache_page(60 * 10))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ServiceDetailView(RetrieveUpdateDestroyAPIView):
    
    serializer_class = ServiceSerializer
    queryset = Service.objects.select_related("profile").filter(is_active=True, is_deleted=False)
    
    def check_object_permissions(self, request, obj):
        if request.method in ("put", "patch", "delete"):
            if not obj.can_edit(request.user):
                raise PermissionDenied()
        return super().check_object_permissions(request, obj)

    
    @transaction.atomic()
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @transaction.atomic()
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, Service):
            instance.soft_delete()
        return Response(data={"detail": "Service deleted successfully", "status": "success"}, status=status.HTTP_204_NO_CONTENT)



        

        
