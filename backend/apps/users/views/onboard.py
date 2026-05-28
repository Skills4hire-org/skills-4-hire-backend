from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from ..serializers.onboard import OnboardingSerializer
from ..serializers.profiles import ProviderProfileUpdateCreateSerializer


class OnboardViewSet(viewsets.ModelViewSet):

    http_method_names = ['post']
    serializer_class =  OnboardingSerializer
    Permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user_profile = serializer.save()
        user = request.user
        return Response(
            {"status": "onboard complete", "is_provider": user.is_provider,
             "is_customer": user.is_customer}, status=status.HTTP_201_CREATED)


class OnboardCompleteViewSet(viewsets.GenericViewSet):
    http_method_names = ['patch']
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProviderProfileUpdateCreateSerializer

    @action(detail=False, methods=['patch'], url_path='')
    def complete(self, request, *args, **kwargs):
        user = request.user
        if not user.is_provider:
            return Response(data={'status': False, "details": "Only providers can use this view"}, status=400)
        
        profile = getattr(user.profile, "provider_profile", "/")
        serializer = self.serializer_class(profile, data=request.data, context={"request": request}, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response({"status": "profile updated", "profile_id": profile.profile_id}, status=status.HTTP_200_OK)