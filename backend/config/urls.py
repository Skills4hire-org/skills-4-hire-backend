
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from .services import health, check_docker_update, test_email, get_banks
from apps.core.views import BaseSearch
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# ADMIN view and health checks
urlpatterns = [
    path('aduser-skills4hire/', admin.site.urls),
    path("health/", health, name="health"),
    # path("docker/", check_docker_update, name="docker"),
    path("email/", test_email, name='test'),
    path('banks/', get_banks, name='get_banks'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

]

# App level url config
urlpatterns += [
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.posts.urls")),
    path("api/v1/", include("apps.ratings.urls")),
    path("api/v1/", include("apps.bookings.urls")),
    path("api/v1/", include("apps.notification.urls")),
    path("api/v1/", include("apps.chats.urls")),
    path("api/v1/", include('apps.wallet.urls')),
    path("api/v1/", include("apps.referral.urls")),
    path("api/admin/", include("apps.admin.urls")),
    path("api/v1/search/", BaseSearch.as_view(), name='search')
    # path("rest/auth/", include("rest_framework.urls"))
]

# Debug toolbar config
DEBUG  = getattr(settings, "DEBUG")
DJANGO_ENV = getattr(settings, "DJANGO_SETTINGS_MODULE", "config.settings.base")

if DEBUG and DJANGO_ENV != "config.settings.prod":
   from debug_toolbar.toolbar import  debug_toolbar_urls
   urlpatterns += debug_toolbar_urls()