from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.core.exceptions import api_response, error_response
from ..serializers.onboard import OnboardingSerializer
from ..serializers.profiles import ProviderProfileUpdateCreateSerializer, BaseProfileCreateSerializer


class OnboardViewSet(viewsets.ModelViewSet):

    http_method_names = ['post']
    serializer_class =  OnboardingSerializer
    Permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user_profile = serializer.save()
        user = request.user
        return api_response(
            data={"is_provider": user.is_provider, "is_customer": user.is_customer},
            message="Onboarding complete",
            status_code=status.HTTP_201_CREATED,
        )


class OnboardCompleteViewSet(viewsets.GenericViewSet):
    http_method_names = ['patch']
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProviderProfileUpdateCreateSerializer

    @action(detail=False, methods=['patch'], url_path='')
    def complete(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = getattr(user.profile, "provider_profile", None)
            if profile is None:
                serializer = BaseProfileCreateSerializer(
                    user.profile, data=request.data['profile'], partial=True, 
                    context={"request": request}
                    )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            else:
                serializer = self.serializer_class(profile, data=request.data, context={"request": request}, partial=True)
                serializer.is_valid(raise_exception=True)
                profile = serializer.save()
            return api_response(
                data={},
                message="Profile updated",
                status_code=status.HTTP_200_OK,
            )
        except Exception as exc:
            return error_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )