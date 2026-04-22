
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response


from ..customer_models import CustomerModel
from ..permissions import IsProfileOwnerOrReadOnly
from ..provider_models import ProviderModel
from ..serializers.profiles import ProviderProfileUpdateCreateSerializer, \
    ProviderProfileDetailSerializer, ProviderProfilePublicSerializer, CustomerProfilePublicSerializer, \
    CustomerCreateUpdateSerializer, CustomerProfileDetailSerializer
from ..profile_services.paginations import ProfilePagination
from ...authentication.serializers import UserReadSerializer


class ProfileSearchView(viewsets.ModelViewSet):

    pagination_class = ProfilePagination
    http_method_names = ['get']
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        print(self.kwargs)
        profile_pk = self.kwargs['pk']
        if profile_pk is None:
            return False
        profile = None
        try:
            provider = ProviderModel.objects.get(pk=profile_pk)
            profile = provider
        except ProviderModel.DoesNotExist:
            customer = CustomerModel.objects.get(pk=profile_pk)
            profile = customer

        return profile

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        query_params = request.query_params.get("search", None)
        if query_params is None:
            return Response("[]", status=status.HTTP_200_OK)
        provider = ProviderModel.objects.filter(
            Q(professional_title__icontains=query_params) |
            Q(profile__display_name__icontains=query_params) |
            Q(availability__icontains=query_params)|
            Q(experience_level__icontains=query_params)
        ).select_related("profile")\
        .prefetch_related("skills", "services")

        customer = CustomerModel.objects.filter(
            Q(profile__display_name__icontains=query_params) |
            Q(industry_name__icontains=query_params)
        ).select_related("profile")

        provider_serializer = ProviderProfileDetailSerializer(provider, many=True).data
        customer_serializer = CustomerProfileDetailSerializer(customer, many=True).data

        combined = provider_serializer + customer_serializer

        page = self.paginate_queryset(combined)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(combined, status=status.HTTP_200_OK)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        if isinstance(profile, ProviderModel):
            return Response(ProviderProfileDetailSerializer(profile).data,
                            status=status.HTTP_200_OK)
        else:
            return Response(CustomerProfileDetailSerializer(profile).data,
                            status=status.HTTP_200_OK)


class ProfileViewSet(viewsets.GenericViewSet):
    permission_classes =  [IsProfileOwnerOrReadOnly]
    http_method_names =  ['get', 'patch']

    def get_serializer_class(self):
        user = self.request.user
        if user.is_provider:
            if self.action in ("partial_update", "me"):
                return ProviderProfileUpdateCreateSerializer
            else:
                return ProviderProfilePublicSerializer

        elif user.is_customer:
            if self.action in ("partial_update", "me"):
                return CustomerCreateUpdateSerializer
            else:
                return CustomerProfilePublicSerializer
        else:
            raise ValueError("Invalid user obj")

    @method_decorator(cache_page(60 * 5))
    @action(methods=['get', 'patch'], detail=False, url_path="me")
    def me(self, request, *args, **kwargs):
        user = request.user
        profile = None

        if user.is_provider:
            profile = user.profile.provider_profile
        elif user.is_customer:
            profile = user.profile.customer_profile
        else:
            return Response(data=UserReadSerializer(user).data, status=status.HTTP_200_OK)
        
        if request.method == "GET":
            if user.is_provider:
                serializer = ProviderProfileDetailSerializer(profile)
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            else:
                serializer = CustomerProfileDetailSerializer(profile)
                return Response(data=serializer.data, status=status.HTTP_200_OK)
        else:
            serializer = self.get_serializer(
                profile, data=request.data,
                context={"request":request}, partial=True
            )
            serializer.is_valid(raise_exception=True)

            updated_profile = serializer.save()
            if user.is_provider:
                output_serializer = ProviderProfileDetailSerializer(updated_profile).data
            else:
                output_serializer = CustomerProfileDetailSerializer(updated_profile).data
            return Response(output_serializer, status=status.HTTP_200_OK)
        return None