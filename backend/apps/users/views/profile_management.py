
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

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
    serializer_class = ProviderProfilePublicSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "professional_title": ['icontains'],
        "min_charge": ['gte', 'lte'],
        "max_charge": ['gte'],
        "reviews__ratings": ["gte", "lte"]
    }

    def get_queryset(self):
        """
        Build search queryset for Provider profiles.
        Uses ?q= query parameter with Django Q objects for OR-based search.
        """
        queryset = ProviderModel.objects.select_related(
            'profile', 'profile__user'
        ).prefetch_related(
            'skills', 'skills__skill', 'skills__skill__category'
        ).filter(
            is_active=True,
            profile__is_active=True
        )

        # Get search query from ?q= parameter
        query = self.request.query_params.get('q', '').strip()

        if query:
            # Build Q object with OR conditions across all relevant fields
            # Search on user name fields, profile fields, provider fields, and skills
            search_q = Q(profile__display_name__icontains=query) | \
                Q(profile__user__username__icontains=query) | \
                Q(profile__city__icontains=query) | \
                Q(profile__country__icontains=query) | \
                Q(professional_title__icontains=query) | \
                Q(headline__icontains=query) | \
                Q(description__icontains=query) | \
                Q(skills__skill__name__icontains=query) | \
                Q(skills__skill__category__name__icontains=query)| \
                Q(services__name__icontains=query) |\
                Q(services__category__name__icontains=query)

            queryset = queryset.filter(search_q).distinct()

            # Order by relevance (featured/top-rated first) then by creation date
            queryset = queryset.order_by('-is_featured', '-is_top_rated', '-created_at')
        else:
            # Default ordering when no search query
            queryset = queryset.order_by('-is_featured', '-is_top_rated', '-created_at')

        return queryset

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

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