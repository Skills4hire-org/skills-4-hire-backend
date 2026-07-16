from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserManagementViewSet


router = DefaultRouter()
 
router.register("users", UserManagementViewSet, basename="user-mangements")

user_managementpatterns = [
    path("", include(router.urls))
]