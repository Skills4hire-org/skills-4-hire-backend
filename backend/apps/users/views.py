from rest_framework import status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import CreateAPIView, DestroyAPIView

from .serializers import (
    OnboardingSerializer,
    BaseProfileUpdateSerializer,
    BaseProfileReadSerializer,
    SwitchRoleSerializer,
)
from .base_model import BaseProfile
from .provider_models import Service
from .permissions import IsProvider, IsSkillOwner

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import transaction
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import F

User = settings.AUTH_USER_MODEL


class OnboardingView(APIView):
    http_method_names = ["post"]
    serializer_class = OnboardingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data.get("role")
        if role is None:
            return Response(data={"detail": "Invalid request: Role cannot be None"}, status=400)
        if request.user.active_role:
            return Response(data={"detail": "Role already selected!"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        request.user.active_role = role.upper()
        request.user.save(update_fields=["active_role"])

        return Response(data={"detail": "Onboarding Complete", "active role": request.user.active_role
                              }, status=status.HTTP_200_OK)


class SwitchRoleView(APIView):
    http_method_names = ["post"]
    serializer_class = SwitchRoleSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data.get("role", None)
        if role is None:
            return Response(data={"detail": "Invalid request, Role cannot be None"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(
            data={"detail": "User role Updated successfully", "status": True, "active_role": request.user.active_role
                  }, status=status.HTTP_200_OK)


switch_role_view = SwitchRoleView.as_view()


class ProfileViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "patch"]
    queryset = (
        BaseProfile.objects.select_related(
            "provider_profile", "customer_profile"
        ).prefetch_related(
            "address", "avater"
        )
    )

    def get_queryset(self):
        return self.queryset.all().filter(is_active=True, is_deleted=False)

    def get_permissions(self):
        if self.action == "list":
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ("partial_update", "update"):
            return BaseProfileUpdateSerializer
        return BaseProfileReadSerializer

    @method_decorator(transaction.atomic)
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance != request.user.profile:
            raise PermissionDenied()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={"detail": "Profile updated successfully", "status": "success", "data": serializer.data
                              }, status=status.HTTP_200_OK)

    @method_decorator(cache_page(60 * 15))
    @action(methods=["get"], detail=False, url_path="me")
    def me(self, request):
        user_profile = get_object_or_404(self.get_queryset(), user=request.user, is_active=True)
        serializer = self.get_serializer(user_profile)
        return Response(data={"status": "success", "data": serializer.data
                              }, status=status.HTTP_200_OK)

    @method_decorator(cache_page(60 * 15))  # cache view for 15 minutes
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

