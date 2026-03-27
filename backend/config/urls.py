
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from .services import health, check_docker_update, test_email
from .drf_yasg import get_swagger_view

# ADMIN view and health checks
urlpatterns = [
    path('admin/', admin.site.urls),
    path("health/", health, name="health"),
    path("docker/", check_docker_update, name="docker"),
    path("email/", test_email, name='test')
]
# Project Documentation
urlpatterns += [
    path("docs/", get_swagger_view().with_ui("swagger", cache_timeout=0), name="swagger-documentation"),
    path("re_docs/", get_swagger_view().with_ui("redoc", cache_timeout=0), name="redoc-documentation"),
]

# App level url config
urlpatterns += [
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.posts.urls")),
    path("api/v1/", include("apps.ratings.urls")),
    path("api/v1/", include("apps.bookings.urls")),
    path("api/v1/", include("apps.notification.urls")),
    path("api/v1/", include("apps.chats.urls"))
    # path("rest/auth/", include("rest_framework.urls"))
]

# Debug toolbar config
DEBUG  = getattr(settings, "DEBUG")
DJANGO_ENV = getattr(settings, "DJANGO_SETTINGS_MODULE", "config.settings.base")

if DEBUG and DJANGO_ENV != "config.settings.prod":
   from debug_toolbar.toolbar import  debug_toolbar_urls
   urlpatterns += [
    path("silk/", include("silk.urls", namespace="silk")),
]
   urlpatterns += debug_toolbar_urls()