from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def get_swagger_view():
    """" A function to get api swagger documatation"""
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

    return schema_view
