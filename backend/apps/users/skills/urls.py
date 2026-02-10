from django.urls import path

from . import views

skills_urlpatterns = [
    path("<uuid:profile_pk>/skills/", views.SkillView.as_view(), name='skill_view'),
    path("<uuid:profile_pk>/skills/<uuid:pk>", views.SkillDetailView.as_view(), name='skill_view'),
]