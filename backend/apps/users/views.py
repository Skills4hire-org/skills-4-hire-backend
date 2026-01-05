from rest_framework import status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import BaseProfileSerializer, ProviderProfileSerializer, ProviderProfileSerializerOut
from .base_model import BaseProfile
from django.shortcuts import get_object_or_404
from .provider_models import ProviderModel
from django.conf import settings

User = settings.AUTH_USER_MODEL




class BaseProfileView(APIView):
    http_method_names = ["patch", "get"]
    permission_classes = [permissions.AllowAny]
    serializer_class = BaseProfileSerializer

    def get(self, request, *args, **kwargs):
        base_profile = request.user.profile

        serializer = self.serializer_class(base_profile)
        return Response(serializer.data)

        return base_profile

    def patch(self, request, *args, **kwargs):

        try:
            serializer = self.serializer_class(request.user.profile, data=request.data, partial=True)

            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({
                "detail": f"error: {str(exc)}"
            }, status=status.HTTP_400_BAD_REQUEST)

base_profile_view = BaseProfileView.as_view()

class ProviderProfileView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post", "patch", "delete", "get"]


    def get_serializer_class(self, request, *args, **kwargs):
        if self.action == "list":
            return ProviderProfileSerializerOut(*args, **kwargs)
        return ProviderProfileSerializer(*args, **kwargs)


    def get_queryset(self):
        try:
            profile = BaseProfile.objects.prefetch_related("provider_profile")
        except Exception as exc:
            return 
        return profile


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
   
        user_profile = queryset.filter(user=request.user).first()
        if user_profile is None:
            return Response({
                "detail": "User Profile Not found!"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(user_profile)

        return Response({
            "success": True,
            "detail": serializer.data
        }, status=status.HTTP_200_OK)






    def create(self, request, *args, **kwarags):
        try:
            base_profile = request.user.profile
        except (Exception, BaseProfile.DoesNotExist) as exc:
            return Response({
                "detail": f"error: {exc}"
            })

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(profile=base_profile)

        # Update the user role to provider
        request.user.role = User.RoleChoices.SERVICE_PROVIDER
        request.user.save()

        return Response({
            "success": True,
            "detail": serializer.data
        }, status=status.HTTP_201_CREATED)



