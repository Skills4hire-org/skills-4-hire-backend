from rest_framework import viewsets, permissions,status
from rest_framework.decorators import action

from apps.core.exceptions import api_response

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

    @action(methods=["GET"], detail=False, url_path="referrals")
    def referral(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs)
        return api_response(
            data={"referrals": serializer.data},
            message="Referral code retrieved successfully",
            status_code=status.HTTP_200_OK,
        )

class ReferralTransactionViewSet(viewsets.ModelViewSet):

    permission_classes  = [permissions.IsAuthenticated]
    serializer_class = ReferralWithdrawalSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        
        local_bank = request.query_params.get("local_bank", False)
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "local_bank": local_bank})
        
        serializer.is_valid(raise_exception=True)

        valid_data = serializer.validated_data
        idempotency_key = valid_data['idempotency_key']

        existing  = ReferralTransactions.objects.filter(
            user=request.user, idempotency_key=idempotency_key
        ).first()

        if existing: 
            logger.info(
                "Found existing transaction for this referral withdrawal"
            )
            serializer = ReferralWithdrawalListSerializer(existing)
            return api_response(
                data={"transaction": serializer.data},
                message="Found existing referral transaction",
                status_code=status.HTTP_200_OK,
            )
        
        save_instance = serializer.save()

        serializer = ReferralWithdrawalListSerializer(save_instance)
        return api_response(
            data={"transaction": serializer.data},
            message="Referral transfer initialized",
            status_code=status.HTTP_201_CREATED,
        )






    





