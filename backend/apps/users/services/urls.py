from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ServiceViewSet, ServiceCategoryViewSet

router = DefaultRouter()
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"services-categories", ServiceCategoryViewSet, basename="category")

service_urlpatterns = [
    path("", include(router.urls)),
]