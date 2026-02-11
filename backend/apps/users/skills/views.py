from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from django.db import transaction
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from .serializers import SkillReadSerializer, SkillSerializer, ProviderSkills
from ..permissions import IsProvider, IsSkillOwner

class SkillView(ListCreateAPIView):
    permission_classes  = [permissions.IsAuthenticated, IsProvider]

    def get_serializer_class(self):
        if self.request.method =='post':
            return SkillSerializer
        return SkillReadSerializer
    
    queryset = (
        ProviderSkills.objects.select_related("category", "profile")
    )
    def get_queryset(self):
        qs = self.filter_queryset(self.queryset)

        user_profile = getattr(self.request.user.profile, "provider_profile")
        if user_profile is None:
            return None
        qs = qs.filter(profile=user_profile, is_active=True, is_deleted=False)
        return qs
    
    @method_decorator(cache_page(60 * 10))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        user_profile_pk = kwargs.get("profile_pk")
        if request.user.profile.pk != user_profile_pk:
            raise PermissionDenied()
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "success", "data": serializer.validated_data}, status=status.HTTP_201_CREATED)

class SkillDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSkillOwner]

    queryset = (
        ProviderSkills.objects.select_related("category", "profile")
    )
    def get_serializer_class(self):
        if self.request.method =='post':
            return SkillSerializer
        return SkillReadSerializer
    
    def destroy(self, request, *args, **kwargs):
        skill_instance = self.get_object()
        if not isinstance(skill_instance, ProviderSkills):
            return Response({"status": "error", "message": "Invalid request. Not a valid skill instance"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            skill_instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

