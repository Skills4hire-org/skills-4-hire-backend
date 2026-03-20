
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CategoryListView, SkillListView, ProviderSkillViewSet

router = DefaultRouter()

router.register('skills', ProviderSkillViewSet, basename="provider_skill")

skills_urlpatterns = [
    path("providers/categories/", CategoryListView.as_view(), name="category-list"),
    path("providers/skills/", SkillListView.as_view(), name="skill-list"),
    path("me/", include(router.urls)),
]