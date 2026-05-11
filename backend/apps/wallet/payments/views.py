from rest_framework import viewsets, permissions, status
from rest_framework.response import Response


from ..serializers import (
    BankAccountSerializer, RessolveBankSerializer,
    TransferRecepientSerializer
)

from ..models import BankAccount

import logging

logger = logging.getLogger(__name__)

class BankAccountViewSet(viewsets.ModelViewSet):
    http_method_names = ['post', "get"]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return RessolveBankSerializer
        return BankAccountSerializer
    
    def get_queryset(self):
        queryset = (
            BankAccount.objects.filter(user=self.request.user, is_active=True)
            .select_related("user")
        )
        return queryset

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        valid_data = serializer.validated_data

        account_number = valid_data['account_number']
        bank_code = valid_data['bank_code']
        user = request.user

        existing = BankAccount.objects.filter(
            account_number=account_number, bank_code=bank_code,
            user=user
        ).first()

        if existing:
            logger.info("Found Existing bank account")
            return Response({
                "status": True,
                "details": "Found Bank Account",
                "data": BankAccountSerializer(existing).data
            })


        bank_account = serializer.save()

        return Response(
            {
                "status": True,
                "message": "Bank account added successfully.",
                "data": BankAccountSerializer(bank_account).data,
            },
            status=status.HTTP_201_CREATED,
        )

class TransferViewSet(viewsets.ModelViewSet):
    http_method_names = ["post"]
    serializer_class = TransferRecepientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        "overide create to return appropriate response"

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        # return bank account details if recipient code already exists

        account_number, bank_code = validated_data['account_number'], validated_data['bank_code']
        user = request.user
        existing = BankAccount.objects.filter(
            account_number=account_number, bank_code=bank_code,
            user=user
        ).first()
        if existing and existing.recipient_code is not None:
            logger.info("Found Existing bank account")
            return Response({
                "status": True,
                "details": "Found Bank Account",
                "data": BankAccountSerializer(existing).data
            })
        
        instance = serializer.save()
        return  Response({
            "status": True,
            "details": "Transfer code added",
            "data": BankAccountSerializer(instance).data
        })
    

