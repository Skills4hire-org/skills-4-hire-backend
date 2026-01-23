
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from .services import health, check_docker_update
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Skills 4 Hire API",
        default_version="v1",
        contact=openapi.Contact(name="Ogenna Israel", email="ogennaisrael@gmail.com"),
        license=openapi.License(name="BSC License")
    ),
    permission_classes=[permissions.AllowAny],
    public=True
)


# ADMIN view and health checks
urlpatterns = [
    path('admin/', admin.site.urls),
    path("health/", health, name="health"),
    path("docker/", check_docker_update, name="docker")
]
# Project Documentation
urlpatterns += [
    path("docs/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-documentation"),
    path("re_docs/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc-documentation"),
]

# App level url config
urlpatterns += [
    path("api/v1/", include("apps.authentication.urls")),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.posts.urls")),
    path("api/v1/", include("apps.ratings.urls")),
    path("api/v1/", include("apps.bookings.urls")),
]

# Debug toolbar config
DEBUG  = getattr(settings, "DEBUG")
DJANGO_ENV = getattr(settings, "DJANGO_SETTINGS_MODULE", "config.settings.dev")

if DEBUG and DJANGO_ENV != "config.settings.prod":
   from debug_toolbar.toolbar import  debug_toolbar_urls
   urlpatterns += debug_toolbar_urls()
