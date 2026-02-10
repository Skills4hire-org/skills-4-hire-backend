from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .serializers import AddresSerializer, Address
from .permissions import IsOwnerOrReadOnly

from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db import transaction


class AddressView(ListCreateAPIView):

    serializer_class = AddresSerializer

    permission_classes = [permissions.IsAuthenticated]
    queryset = (
        Address.objects.select_related("profile")
    )

    def check_object_permissions(self, request, obj):
        if self.request.method in ("post","get"):
            profile_pk = self.kwargs.get("profile_pk")
            if request.user.profile.pk != profile_pk:
                raise PermissionDenied()
        return super().check_object_permissions(request, obj)
    
    def get_queryset(self):
        qs = self.filter_queryset(self.queryset())
        user_address = qs.filter(profile=self.request.profile, is_active=True, is_deleted=False)
        if user_address is None:
            return None
        return user_address

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        profile_pk = kwargs.get("profile_pk")
        serializer = self.get_serializer(data=request.data, context={"request": request, "profile_pk": profile_pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "success", "data": serializer.validated_data}, 
                        status=status.HTTP_201_CREATED)


class AddressDetailView(RetrieveUpdateDestroyAPIView):
    queryset =(
        Address.objects.select_related("profile").filter(is_active=True, is_deleted=False)
    )

    serializer_class = AddresSerializer

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        address_instance = self.get_object()
        if not isinstance(address_instance, Address):
            return Response({"status": "error", "message": "Invalid request. Not a valid address instance"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            address_instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
