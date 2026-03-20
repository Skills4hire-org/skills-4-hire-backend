from rest_framework import generics, permissions, filters

from .models import Category, Skill
from .serializers import SkillSerializer, CategorySerializer, ProviderSkillCreateSerializer, \
    ProviderSkillDetailSerializer, ProviderSkillListSerializer
from .pagination import StandardPagination

from django_filters.rest_framework import DjangoFilterBackend

from ..permissions import IsProvider
from ..provider_models import ProviderSkill



class CategoryListView(generics.ListAPIView):
    """GET /api/v1/providers/categories/"""
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Category.active_manager.all()

class SkillListView(generics.ListAPIView):
    """GET /api/v1/providers/skills/?search=python&category=1"""
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Skill.active_objects.select_related("category")
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    filterset_fields = ["category__name"]
    pagination_class = StandardPagination


from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend


class ProviderSkillViewSet(viewsets.ModelViewSet):

    http_method_names = ['post', 'get', 'patch', 'delete']

    permission_classes = [IsProvider]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['proficiency', 'is_primary', 'skill__category']
    search_fields = ['skill__name', 'description']
    ordering_fields = ['sort_order', 'years_used', 'created_at']


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
        2. select_related('skill') joins the skill table to prevent N+1 queries.
        """
        return ProviderSkill.objects.filter(
            provider_profile__profile=self.request.user.profile
        ).select_related('skill')

    def perform_create(self, serializer):
        """Auto-assign the provider profile from the authenticated user."""
        serializer.save(provider_profile=self.request.user.profile.provider_profile)

    def perform_destroy(self, instance):
        instance.soft_delete()