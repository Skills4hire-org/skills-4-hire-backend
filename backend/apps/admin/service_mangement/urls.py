from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ServiceCategoryManagementViewset

router = DefaultRouter()

router.register("service", ServiceCategoryManagementViewset, basename="service-management")

service_urlpatterns = [
    path("", include(router.urls))
]
