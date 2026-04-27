from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ReferralCode, ReferralTransactions
from .serializers import (
    ReferralCodeSerializer, ReferralWithdrawalSerializer,
    ReferralWithdrawalListSerializer
)


import  logging
logger = logging.getLogger(__name__)

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
        serializer = self.get_serializer(qs)
        return Response(status=200, data={"status": True, "details": serializer.data})

class ReferralTransactionViewSet(viewsets.ModelViewSet):

    permission_classes  = [permissions.IsAuthenticated]
    serializer_class = ReferralWithdrawalSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        valid_data = serializer.validated_data
        idempotency_key = valid_data['idempotency_key']

        existing  = ReferralTransactions.objects.filter(
            user=request.user, idempotency_key=idempotency_key
        ).first()

        if  existing: 
            logger.info(
                "Found existing transaction for this referral with drawal"
            )
            serializer = ReferralWithdrawalListSerializer(existing)
            return Response({
                "status": False,
                "details": "Found Existing Transaction",
                "data": serializer.data
            })
        
        save_instance = serializer.save()

        serializer = ReferralWithdrawalListSerializer(save_instance)
        return Response({
            "status": True,
            "detaial": "Transfer Initialized",
            "data": serializer.data
        })






    





