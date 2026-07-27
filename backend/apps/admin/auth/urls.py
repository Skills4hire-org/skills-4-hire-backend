from rest_framework.routers import DefaultRouter

from django.urls import path, include
from .views import AdminRegistrationViewset, AdminLoginView

router = DefaultRouter()

router.register("register", AdminRegistrationViewset, basename="admin-registration")

urlpatterns = [
    path("", include(router.urls)),
    path("login/", AdminLoginView.as_view(), name="admin-login")
]