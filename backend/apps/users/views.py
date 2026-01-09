from rest_framework import status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (
    ProviderProfileSerializer, 
    OnboardingSerializer, 
    BaseProfileUpdateSerializer, 
    BaseProfileReadSerializer,
    AddresSerializer,
    AvaterSerializer,
    ProviderSkillSerializer
)
from .base_model import BaseProfile, Address, Avater
from django.shortcuts import get_object_or_404
from .provider_models import ProviderModel, ProviderSkills
from .client_models import ClientModel
from django.conf import settings
from .services.provider_service import ProviderService
from django.db import transaction
from rest_framework.decorators import action
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .permissions import IsProvider, IsSkillOwner

User = settings.AUTH_USER_MODEL

class OnboardingView(APIView):
    http_method_names = ["post"]
    serializer_class = OnboardingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data.get("role")

        if role is None:
            return Response(data={
                "detail": "Invalid request: Role cannot be None"
            },status=400)


        if request.user.active_role:
            return Response(data={
                "detailt": "Role already selected!"
            }, status=status.HTTP_400_BAD_REQUEST)


        base_profile = request.user.profile
        match role.upper():
            case "SERVICE_PROVIDER": 
                provider_profile = ProviderModel(profile=base_profile)
                request.user.is_provider = True
                provider_profile.save()

            case "CLIENT":
                client_profile = ClientModel(profile=base_profile)
                request.user.is_client = True
                client_profile.save()

            case "BOTH":
                provider_profile = ProviderModel(profile=base_profile)
                request.user.is_provider = True
                request.user.is_client = True

                provider_profile.save()


            case _:
                return Response(data={
                    "detail": "Invalid role provided"
                }, status=status.HTTP_400_BAD_REQUEST)


        if role.upper() == "BOTH":
            role = "SERVICE_PROVIDER"

        request.user.active_role = role
        request.user.save(update_fields=["active_role"])

        return Response(data={
            "detail": "Onboarding Complete",
            "active role": request.user.active_role
        }, status=status.HTTP_200_OK)


class SwitchRoleView(APIView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):

        role = request.data.get("role")

        if role is None:
            return Response(data={
                "detail": "role cannot be None"
            }, status=status.HTTP_400_BAD_REQUEST)
        allowed_roles = ("service_provider", "client")

        if  request.user.active_role == role.upper():
            return Response(data={
                "detail": f"you are already  in the {role} view"
            }, status=200)
        
        if role.lower() not in allowed_roles:
            return Response(data={
                "detail": "Specifield role is not included in the allowed roles"
            }, status=status.HTTP_400_BAD_REQUEST)

        request.user.active_role = role.upper()
        request.user.save(update_fields=["active_role"])

        return Response(data={
            "detail":  "Role updated",
            "active_role": request.user.active_role
        }, status=status.HTTP_200_OK)

switch_role_view = SwitchRoleView.as_view()

class ProfileView(APIView):
    http_method_names = ["patch"]

    serializer_class = BaseProfileUpdateSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data, context={
            "request": request
        }, partial=True)

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        
        # update base profile
        base_profile = request.user.profile
        with transaction.atomic():
            for fields in ("gender", "bio", "location"):
                if fields in data:
                    setattr(base_profile, fields, data[fields])

            base_profile.save()
            
        # update role profiles
        if request.user.active_role == "SERVICE_PROVIDER" and "provider_profile" in data:
            provider_profile = base_profile.provider_profile
            with transaction.atomic():
                for fields, value in data["provider_profile"].items():
                    setattr(provider_profile, fields, value)

                provider_profile.save()
            
    
        if request.user.active_role == "CLIENT" and "client_profile" in data:
    
            client_profile = base_profile.client_profile

            with transaction.atomic():
                for fields, value in data["client_profile"].items():
                    setattr(client_profile, fields, value)

                client_profile.save()

        return Response(data={
            "detail": "Profile Updated Successfully",
            "success": True
        }, status=status.HTTP_200_OK)


profile_view = ProfileView.as_view()
    


class ProfileReadView(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "delete"]

    
    def get_queryset(self):

        profile = (
            BaseProfile.objects.select_related(
                "provider_profile", "client_profile"
                ).prefetch_related(
                    "address", "avaters"
                )
    
        )

        return profile

    serializer_class = BaseProfileReadSerializer

    @action(methods=["get"], detail=False, url_path="me")
    def me(self, request):

        user_profile = get_object_or_404(
            self.get_queryset(),
            user=request.user
        )

        serializer = self.get_serializer(user_profile)

        return Response(data={
            "status": "successful",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    

    @method_decorator(cache_page(60 * 15)) # cache view for 15 minutes
    @action(methods=["get"], detail=True)
    def public(self, request, pk=None):

        profile = get_object_or_404(
            self.get_queryset(),
            pk=pk
        )

        serializer = self.get_serializer(profile)
        return Response(data={
            "status": "successful",
            "data": serializer.data
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
        return Response({
            "detail": "Profile photo saved",
            "status": "success"
        }, status=status.HTTP_201_CREATED)


    @action(methods=["delete"], detail=False, url_path="avater")
    def delete_avater(self, request, *args, **kwargs):
        profile = request.user.profile

        profile.avaters.avater = None
        profile.avaters.avater_public_id = None
        profile.avaters.description = None

        profile.avaters.save(update_fields=["avater", "avater_public_id", "description"])
        return Response(data={
            "detail": "photo deleted",
            "status": "deleted"
        }, status=status.HTTP_204_NO_CONTENT)
    

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddresSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        serializer.save(profile=self.user.profile)

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response(data={
            "detail": "Address uploaded",
            "status": "succcess"
        }, status=status.HTTP_201_CREATED)


    def get_queryset(self):
        address = Address.objects.select_related(
            "profile"
            ).filter(
                profile=self.request.user.profile
                )
        return address


class ProviderSkillViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderSkillSerializer

    def get_queryset(self):
        skills = ProviderSkills.objects.select_related(
            "profile", "skill"
        ).filter(
            profile=self.request.user.profile.provider_profile if hasattr(
                self.request.user.profile, "provider_profile"
            ) else None
        )
        return skills
    
    def get_permissions(self):
        if self.methods in ("put", "patch", "delete"):
            permission_classes = [permissions.IsAuthenticated, IsProvider, IsSkillOwner]
        if self.methods in ("post"):
            permission_classes = [permissions.IsAuthenticated, IsProvider]

        else:
            permission_classes = [permissions.IsAuthenticated]

        return [perm() for perm in permission_classes]
    
    
    def create(self, request, *args, **kwargs):
        """
        Create a new provider skill associated with the authenticated user's provider profile.
        """

        skill_name = request.query_params.get("skill_name")

        serializer = self.get_serializer(data=request.data, context={
            "request": request,
            "skill_name": skill_name
        })

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(data={
            "detail": "Skill added successfully",
            "status": "success"
        }, status=status.HTTP_201_CREATED)
    

        
