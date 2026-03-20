from rest_framework import viewsets, status, permissions
from rest_framework.response import Response

from ..serializers.onboard import OnboardingSerializer


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



