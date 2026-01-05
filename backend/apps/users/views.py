from rest_framework import status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ProviderProfileSerializer, OnboardingSerializer, BaseProfileUpdateSerializer, BaseProfileReadSerializer
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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):

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

        if role == User.RoleChoices.SERVICE_PROVIDER: 
            provider_profile = ProviderModel(profile=base_profile)
            provider_profile.save()

        elif role == User.RoleChoices.CLIENT:
            client_profile = ClientModel(profile=base_profile)
            client_profile.save()

        request.user.role = role
        request.user.save()

        return Response(data={
            "detail": "Onboarding Complete"
        }, status=status.HTTP_200_OK)


onboarding_view = OnboardingView.as_view()



class ProfileView(APIView):
    http_method_names = ["patch"]

    serializer_class = BaseProfileUpdateSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data, context={
            "request": request
        })

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
        if request.user.role == User.RoleChoices.SERVICE_PROVIDER and "provider_profile" in data:
            provider_profile = base_profile.provider_profile
            with transaction.atomic():
                for fields, value in data["provider_profile"].items():
                    setattr(provider_profile, fields, value)

                provider_profile.save()
        if request.user.role == User.RoleChoices.CLIENT and "clent_profile" in data:
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
                    "address", "avater"
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

        serializer = self.get_serializer(user_profile, many=True)

        return Response(data={
            "status": "successful",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    

    @method_decorator(cache_page(60 * 15)) # cache view for 15 minutes
    @action(methods=["get"], detail=False)
    def public(self, request, pk=None):

        profile = get_object_or_404(
            self.get_queryset(),
            pk=pk
        )

        serializer = self.get_serializer(profile, many=True)
        return Response(data={
            "status": "successful",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


















