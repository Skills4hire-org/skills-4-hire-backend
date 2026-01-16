from rest_framework import status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from .serializers import (
    ProviderProfileSerializer, 
    OnboardingSerializer, 
    BaseProfileUpdateSerializer, 
    BaseProfileReadSerializer,
    AddresSerializer,
    AvaterSerializer,
    ProviderSkillSerializer,
    SwitchRoleSerializer,
    ServiceSerializer
)
from .base_model import BaseProfile, Address, Avater
from .provider_models import ProviderModel, ProviderSkills, Service
from .customer_models import CustomerModel
from .services.provider_service import ProviderService
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
            return Response(data={"detail": "Invalid request: Role cannot be None"},status=400)
        if request.user.active_role:
            return Response(data={"detailt": "Role already selected!"}, status=status.HTTP_400_BAD_REQUEST)
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
        return Response(data={"detail": "User role Updated successfully", "status": True, "active_role": request.user.active_role
        }, status=status.HTTP_200_OK)
switch_role_view = SwitchRoleView.as_view()

class ProfileView(APIView):
    http_method_names = ["patch"]
    serializer_class = BaseProfileUpdateSerializer
    def patch(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={"detail": "Profile updated ", "statis": True, "active_role": request.user.active_role,
        }, status=status.HTTP_200_OK)

profile_view = ProfileView.as_view()
    
class ProfileReadView(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "delete"]
    queryset = (
            BaseProfile.objects.select_related(
                "provider_profile", "customer_profile"
                ).prefetch_related(
                    "address", "avater"
                )
    )
    def get_queryset(self):
        return self.queryset.all().filter(is_active=True, is_deleted=False)
    
    serializer_class = BaseProfileReadSerializer

    @method_decorator(cache_page(60 * 15))
    @action(methods=["get"], detail=False, url_path="me")
    def me(self, request):
        user_profile = get_object_or_404(self.get_queryset(), user=request.user)
        serializer = self.get_serializer(user_profile)
        return Response(data={"status": "success", "data": serializer.data
        }, status=status.HTTP_200_OK)

    @method_decorator(cache_page(60 * 15)) # cache view for 15 minutes
    @action(methods=["get"], detail=True)
    def public(self, request, pk=None):
        profile = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(profile)
        return Response(data={"status": "success", "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=False, url_path="avater/upload")
    def upload_avater(self, request, *args, **kwargs):
        serializer = AvaterSerializer(
            request.user.profile.avaters if request.user.profile.avater else None,
            data=request.data,
            partial=True
        )   
        serializer.is_valid(raise_exception=True)
        serializer.save(profile=request.user.profile)
        return Response({"detail": "Profile photo saved", "status": "success"
        }, status=status.HTTP_201_CREATED)


    @action(methods=["delete"], detail=False, url_path="avater")
    def delete_avater(self, request, *args, **kwargs):
        profile = request.user.profile 
        avater = profile.avater if hasattr(profile, "avater") else None
        if avater:
            avater.soft_delete()
        return Response(data={"detail": "Profile avater removed", "status": "success"
        }, status=status.HTTP_204_NO_CONTENT)
    
class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddresSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Address.objects.select_related("profile")
    
    def perform_create(self, serializer):
        serializer.save(profile=self.user.profile)

    def check_object_permissions(self, request, obj):
        if request.method in ("put", "patch", "delete"):
            if not obj.can_edit(request.user):
                raise PermissionDenied("You dont have access to perform this action") 
        return super().check_object_permissions(request, obj)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(data={"detail": "Address uploaded", "status": "success"
        }, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        address = get_object_or_404(self.queryset, profile=self.request.user.profile, is_active=True, is_deleted=False)
        return address
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, Address):
            instance.soft_delete()
            return Response(data={"detail": "Address deleted successfully", "status": "success"}, status=status.HTTP_204_NO_CONTENT)
        
class ProviderSkillViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderSkillSerializer
    permission_classes = [permissions.IsAuthenticated, IsProvider, IsSkillOwner]

    queryset = ProviderSkills.objects.select_related("profile", "skill")
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ProviderSkills.objects.none()
        if not self.request.user.is_authenticated:
            return ProviderSkills.objects.none()  
        skills =self.queryset.filter(profile=self.request.user.profile.provider_profile if hasattr(
            self.request.user.profile, "provider_profile") else None, is_active=True, is_deleted=False)
        return skills
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={"detail": "Skill added successfully", "status": "success"
        }, status=status.HTTP_201_CREATED)
    
    def check_object_permissions(self, request, obj):
        if request.method in ("put", "patch", "delete"):
            if not obj.can_edit(request.user):
                raise PermissionDenied("You can't perform this action")
        return super().check_object_permissions(request, obj)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, ProviderSkills):
            instance.soft_delete()
        return Response({"detail": "Skill deleted successfully", "status": "success"}, status=status.HTTP_204_NO_CONTENT)
    
    
class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    queryset = Service.objects.select_related("profile")
    permission_classes = [permissions.IsAuthenticated, IsProvider, IsSkillOwner]

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(data={"detail": "Service created successfully", "status": "success"
        }, status=status.HTTP_201_CREATED, headers=headers)
    
    def check_object_permissions(self, request, obj):
        if request.method in ("put", "patch", "delete"):
            if not obj.can_edit(request.user):
                raise PermissionDenied("You can't perform this action")
        return super().check_object_permissions(request, obj)
    
    def get_queryset(self):
        qs = self.queryset.all().filter(is_active=True, is_deleted=False)
        if not qs:
            return self.queryset.none()
        return qs
    
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @transaction.atomic()
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @transaction.atomic()
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, Service):
            instance.soft_delete()
        return Response(data={"detail": "Service deleted successfully", "status": "success"}, status=status.HTTP_204_NO_CONTENT)



        

        
