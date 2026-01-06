from rest_framework import status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (
    ProviderProfileSerializer, 
    OnboardingSerializer, 
    BaseProfileUpdateSerializer, 
    BaseProfileReadSerializer
)
from .base_model import BaseProfile
from django.shortcuts import get_object_or_404
from .provider_models import ProviderModel
from .client_models import ClientModel
from django.conf import settings
from .services.provider_service import ProviderService
from django.db import transaction
from rest_framework.decorators import action
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

User = settings.AUTH_USER_MODEL

class OnboardingView(APIView):
    http_method_names = ["post"]
    serializer_class = OnboardingSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data.get("role")

        if role is None:
            return Response(data={
                "detail": "Invalid request: Role cannot be None"
            },status=400)


        if request.user.role:
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

        role = request.data.get("role").lower()
        allowed_roles = ("service_provider", "client")

        if role not in allowed_roles:
            return Response(data={
                "detail": "Specifield role is not inthe allowed role "
            }, status=status.HTTP_400_BAD_REQUEST)

        request.user.active_role = role.upper()
        request.user.save(update_fields=["active_role"])

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
    http_method_names = ["get"]

    
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


class AddressViewSet(viewsets.ModelViewSet):
    pass
