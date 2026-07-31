from django.urls import path, include

from rest_framework.routers import DefaultRouter
from .views import ApplicationCategoryViewset, OpenApplicationViewset

router = DefaultRouter()

router.register("category", ApplicationCategoryViewset, basename='category')
router.register("external", OpenApplicationViewset, basename='open-application')

urlpatterns = [
    path("application/", include(router.urls))
]