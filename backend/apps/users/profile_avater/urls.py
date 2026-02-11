from django.urls import path

from . import views

avater_urlpatterns = [
    path("profile/<uuid:profile_pk>/avater/", views.AvaterManagementView.as_view(), name="avater")
]