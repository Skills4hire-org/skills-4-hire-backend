from rest_framework import generics, permissions, filters, viewsets

from .models import Category, Skill
from .serializers import SkillSerializer, CategorySerializer, ProviderSkillCreateSerializer, \
    ProviderSkillDetailSerializer, ProviderSkillListSerializer
from .pagination import StandardPagination

from django_filters.rest_framework import DjangoFilterBackend

from .permissions import SkillsOwnerPermissions
from ..provider_models import ProviderSkill



class CategoryListView(generics.ListAPIView):
    """GET /api/v1/providers/categories/"""

    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Category.active_manager.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['-name']

class SkillListView(generics.ListAPIView):

    """GET /api/v1/providers/skills/?search=python&category=1"""

    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Skill.active_objects.select_related("category")
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    filterset_fields = ["category__name", 'name']
    pagination_class = StandardPagination


class ProviderSkillViewSet(viewsets.ModelViewSet):

    http_method_names = ['post', 'get', 'patch', 'delete']

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['proficiency', 'is_primary', 'skill__category__name']
    search_fields = ['skill__name', 'description']
    ordering_fields = ["-created_at"]
    pagination_class = StandardPagination
    permission_classes = [SkillsOwnerPermissions]


    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return ProviderSkillCreateSerializer
        elif self.action == 'retrieve':
            return ProviderSkillDetailSerializer
        return ProviderSkillListSerializer

    def get_queryset(self):
        """
        Optimized queryset:
        1. Only returns skills for the logged-in provider.
        """

        user = self.request.user
        if user.is_customer:
            return ProviderSkill.objects.none()
        
        queryset = (
            ProviderSkill.active_objects.filter(
                provider_profile=user.profile.provider_profile
            ).select_related("provider_profile")
        )
        return queryset
    
    def perform_destroy(self, instance):
        instance.soft_delete()