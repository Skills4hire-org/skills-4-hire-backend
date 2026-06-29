
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ..permissions import IsProfileOwnerOrReadOnly
from ..provider_models import ProviderModel
from ...posts.models import PostAttachment
from ...posts.services_T import return_paginated_view
from ...posts.serializers.create import PostAttachmentSerializer
from ..base_model import WorkImages
from ..serializers.profiles import ProviderProfileUpdateCreateSerializer, BaseProfileListSerializer, \
    ProviderProfileDetailSerializer, ProviderProfilePublicSerializer, \
    CustomerCreateUpdateSerializer, CustomerProfileDetailSerializer, CoverPhoto, WorkImagesSerializer
from ..profile_services.paginations import ProfilePagination
from ...authentication.serializers import UserReadSerializer
from ...core.exceptions import api_response, error_response
from ..base_model import BaseProfile
from ..profile_avater.serializers import AvatarCreateSerializer
from ..permissions import IsWorkImageOwnerOrReadOnly

from uuid import UUID

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
    http_method_names =  ['get', 'patch', "delete", "post"]

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
                return CustomerProfileDetailSerializer
        else:
            raise ValueError("Invalid user obj")

    @action(methods=["post", "delete"], detail=False, url_path="avatar") 
    def profile_picture(self, request, *args, **kwargs):
        base_profile: BaseProfile = request.user.profile
        if request.method in ("post", "POST"):
            # either update a picture or add a new one
            serializer = AvatarCreateSerializer(data=request.data, context={"profile": base_profile})
            serializer.is_valid(raise_exception=True)
            data = serializer.save()
            return api_response(
                data=serializer.validated_data,
                message="Profile photo updated successfully",
                status_code=200,
            )
        else:
            avater = getattr(base_profile, "avatar", None)
            if avater is None:
                return error_response(message="No profile is assciated to this account", status_code=status.HTTP_404_NOT_FOUND)
            avater.delete()
            return api_response(data={}, message="success", status_code=status.HTTP_204_NO_CONTENT)
        
    @action(methods=['patch', "delete"], detail=False, url_path="cover-photo")
    def upload_cover_photo(self, request, *args, **kwargs):
        if request.method in ("patch", "PATCH"):
            user_base_profile = request.user.profile
            serializer = CoverPhoto(instance=user_base_profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            cover_letter = serializer.save()
            return api_response(
                data=serializer.validated_data,
                message="Profile cover photo updated successfully",
                status_code=200,
            )
        else:
            base_profile: BaseProfile = request.user.profile
            try:
                base_profile.cover_photo = {}
                base_profile.save()
                return api_response(data={}, status_code=status.HTTP_204_NO_CONTENT)
            except Exception as error:
                return error_response(message="Invalid profile", errors=error, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['get', 'patch'], detail=False, url_path="me")
    def me(self, request, *args, **kwargs):
        user = request.user
        profile = None

        if user.is_provider:
            profile = user.profile.provider_profile
        elif user.is_customer:
            profile = user.profile.customer_profile
        else:
            return api_response(
                data=UserReadSerializer(user).data,
                message="Profile fetched successfully",
                status_code=status.HTTP_200_OK,
            )
        
        if request.method == "GET":
            if user.is_provider:
                serializer = ProviderProfileDetailSerializer(profile, context={'request': request})
                return api_response(
                    data=serializer.data,
                    message="Profile fetched successfully",
                    status_code=status.HTTP_200_OK,
                )
            else:
                serializer = CustomerProfileDetailSerializer(profile, context={"request": request})
                return api_response(
                    data=serializer.data,
                    message="Profile fetched successfully",
                    status_code=status.HTTP_200_OK,
                )
        else:
            serializer = self.get_serializer(
                profile, data=request.data,
                context={"request": request}, partial=True
            )
            serializer.is_valid(raise_exception=True)
            updated_profile = serializer.save()
            return api_response(
                data={},
                message="Profile updated",
                status_code=status.HTTP_200_OK,
            )
        

class WorkImagesViewSet(viewsets.ModelViewSet):
    http_method_names = ['post', "get", "patch", "delete"]
    pagination_class = ProfilePagination
    permission_classes = [IsWorkImageOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == "user_images":
            return WorkImagesSerializer
        elif self.action == "user_activity":
            return PostAttachmentSerializer
        else:
            return WorkImagesSerializer
    
    def get_queryset(self):
        return self.filter_queryset(
            WorkImages.objects.filter(
                profile=self.request.user.profile
                )
                .select_related("profile")
        )

    def create(self, request, *args, **kwargs):
        # overider create function to allow bulk upload 
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(profile=request.user.profile)
        return api_response(
            data={},
            message="Profile images added",
            status_code=status.HTTP_200_OK,
        )
    
    @action(methods=["get"], detail=False, url_path="user/(?P<user_id>[^/.]+)/images")
    def user_images(self, request, user_id: UUID = None):
        images = WorkImages.objects.filter(profile__user__pk=user_id)
        return return_paginated_view(self, images)

    @action(methods=['get'], detail=False, url_path="user/(?P<user_id>[^/.]+)/activity")
    def user_activity(self, request, user_id: UUID = None):
        ''' fetch all images related to the user from posts and comments'''
        images = PostAttachment.objects.filter(
            Q(post__user__pk=user_id) | Q(comment__user__pk=user_id)
        ).select_related("post", 'comment')

        return return_paginated_view(self, images)