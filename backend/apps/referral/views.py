from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ReferralCode
from .serializers import ReferralCodeSerializer


class ReferralViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReferralCodeSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = ReferralCode.objects\
                    .select_related("owner")\
                    .filter(owner=user)
        return queryset.first()

    @action(methods=["GET"], detail=False, url_path="referral")
    def referral(self, request, *args, **kwargs):
        qs = self.get_queryset()
        print(qs)
        serializer = self.get_serializer(qs)
        return Response(status=200, data={"status": True, "details": serializer.data})
    




