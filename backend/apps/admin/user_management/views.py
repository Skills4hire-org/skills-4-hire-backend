from rest_framework import viewsets, filters
from rest_framework.decorators import action

from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models.functions import Lower
from django_filters.rest_framework import DjangoFilterBackend

from ..permissions import IsAdmin, ADMIN_ROLES
from .serializers import UserManagementListSerializer, UserModel, UserManagementDetailSerializer
from ..pagination import AdminPagination
from ...referral.models import Referral
from ...core.exceptions import api_response, error_response
from .services import delete_user_account, suspend_user_account

import logging

logger = logging.getLogger(__name__)
VALID_ADMIN_ACTIONS = ['suspend', "delete"]

class UserManagementViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', "patch", 'delete']
    permission_classes = [IsAdmin]
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = [
        'is_active', "is_provider", "is_customer",
        "active_role"
    ]
    search_fields = [
        "email", "first_name", "last_name", 
    ]

    #overide list to cache querylist
    @method_decorator(cache_page(60 * 10))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = UserModel.objects.prefetch_related("referrals_made").filter(is_deleted=False)
        # exclude admin users
        admin_users = UserModel.objects.annotate(
            role_lower_case=Lower("active_role")
        ).filter(role_lower_case__in=ADMIN_ROLES).values_list("user_id", flat=True)

        queryset = queryset.exclude(user_id__in=admin_users)
        if getattr(self, "request", None) is None:
            return queryset
        return self.filter_queryset(queryset)

    serializer_class = UserManagementDetailSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return UserManagementListSerializer
        return self.serializer_class
    
    @action(methods=['get'], detail=True, url_path='referrals')
    def referrals(self, request):
        # Fetch all referrals for this user
        try:
            user = self.get_object()
            referrals = Referral.objects.select_related(
                "referred"
                ).filter(
                    referrer=user
                    ).order_by('-created_at')
            referred_users = [referral.referred for referral in referrals]
            page = self.paginate_queryset(referrals)
            if page is not None:
                serializer = UserManagementDetailSerializer(referred_users, many=True)
                response = self.get_paginated_response(serializer.data)
                return api_response(data=response)
            
            serializer = UserManagementListSerializer(referred_users, many=True)
            return api_response(data=serializer.data)
        
        except Exception as error:
            logger.error("[admin] Failed fetching referrals: "+ error)
            return error_response(errors=error, status_code=500)
    
    @action(methods=["patch", "delete"], detail=True, url_path=r"(?P<admin_action>[^/.]+)")
    def action(self, request, pk=None, admin_action: str = None):
        try:
            if admin_action not in VALID_ADMIN_ACTIONS:
                logger.info("[admin]: Passed invalid action on user account.")
                return api_response(data={}, message="Invalid Request", status_code=404)
            print(request.method)
            user = self.get_object()
            if admin_action.lower() == "delete" and request.method == "DELETE":
                # delete user account permanently/ 
                logger.info(f"[admin]: Deleting User account: Email:: {user.email}: Id :: {user.pk}")
                result = delete_user_account(user)
                return api_response(data={}, message="Successfuly deleted user account", status_code=204)
            
            elif admin_action.lower() == 'suspend' and request.method == "PATCH":
                logger.info(f"[admin]: suspending user account: Email: {user.email}, Id: {user.pk}")
                result = suspend_user_account(user)
                return api_response(data={}, message="successfully suspended user account")
            
            else:
                logger.info(f"[admin]: failed all admin action")
                return api_response(data={}, message="Invalid Request", status_code=400)
        except Exception as error:
            logger.error(f"[admin]: Error {admin_action} user acount: Reason: {error}")
            return error_response(message="Internal Server Error", errors= error, status=500)