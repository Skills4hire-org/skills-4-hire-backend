from django.urls import path

from . import views

service_urlpatterns = [
    path("profile/<uuid:profile_pk>/services/", views.ServiceViewSet.as_view(), name="service"),
    path("services/<uuid:pk>/", views.ServiceDetailView.as_view(), name="service")
]