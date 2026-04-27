from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ReviewViewSet

routers = DefaultRouter()

routers.register("reviews", ReviewViewSet, basename='review')

urlpatterns = [
    path("", include(routers.urls))
]

