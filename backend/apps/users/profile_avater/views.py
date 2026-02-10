from rest_framework.generics import CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import PermissionDenied

from .serializers import AvaterSerializer
from ..base_model import BaseProfile
from .permissions import IsOwner

from django.shortcuts import get_object_or_404

class AvaterManagementView(CreateAPIView, DestroyAPIView, UpdateAPIView):
    serializer_class = AvaterSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_object(self):
        profile_pk = self.kwargs.get("profile_pk")
        base_profile = get_object_or_404(BaseProfile, pk=profile_pk)
        self.check_object_permissions(self.request, base_profile)
        return base_profile
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})   
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Profile photo saved", "status": "success"
        }, status=status.HTTP_201_CREATED)

    
    def destroy(self, request, *args, **kwargs):
        profile = self.get_object()
        avater = profile.avater if hasattr(profile, "avater") else None
        if avater:
            avater.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise PermissionDenied()
    
