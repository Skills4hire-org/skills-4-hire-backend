from django.urls import path

from . import views

address_urlpatterns = [
    path("<uuid:profile_pk>/address", views.AddressView.as_view(), name="address"),
    path("<uuid:profile_pk>/address/<uuid:pk>/", views.AddressDetailView.as_view(), name="address-detail")
]