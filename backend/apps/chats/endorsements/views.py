from rest_framework import viewsets, permissions,status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied

from .serializers import (
    EndorsementCreateSerializer, EndorsementSerializer,
    get_or_none, ProviderModel, EndorsementDetailSerializer
)
from .models import Endorsements
from .permissions import IsEndorsementCreateUser, IsSubject
from .paginations import EndorsementPagination

    
class EndorsementViewSet(viewsets.ModelViewSet):

    http_method_names = ['post', 'patch', 'delete']

    queryset = (
        Endorsements.objects.filter(
                is_active=True
            )
            .select_related("endorsed_by", 'provider')
            .order_by("-endorsed_at")
        )
    
    def get_serializer_class(self):
        if self.action in ("create", 'partial_update'):
            return EndorsementCreateSerializer
        return None
    
    def get_permissions(self):
        if self.action in ("create", 'partial_update'):
            return [IsEndorsementCreateUser()]
        if self.action == 'destroy':
            return [permissions.IsAdminUser()]
        if self.action == 'hide':
            return [IsSubject()]
        return [permissions.IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        # bypass the create method to structure the response
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        saved_endorsement = serializer.save()
        output_serializer = EndorsementSerializer(saved_endorsement)
        
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_endorsement = serializer.save()
        return Response(EndorsementSerializer(updated_endorsement).data, 
                        status=status.HTTP_200_OK)
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    def perform_hide(self, instacne):
        instacne.is_hidden = True
        instacne.save(update_fields=['is_hidden'])

    @action(methods=['patch'], detail=True, url_path='hide')
    def hide(self, request, *args, **kwargs):
        endorsement_obj = self.get_object()
        user = request.user
        if  user != endorsement_obj.provider.profile.user:
            raise PermissionDenied()
        self.perform_hide(instacne=endorsement_obj)

        return Response(status=status.HTTP_200_OK)


class EndorsementDetailViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EndorsementPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return EndorsementSerializer
        if self.action == 'retrieve':
            return EndorsementDetailSerializer
        return None
    
    def get_user_endorsements(self, provider_profile):
        user = self.request.user
        endorsements = (
            Endorsements.objects.filter(
                is_active=True, provider=provider_profile
            )
            .select_related("endorsed_by", 'provider')
            .order_by("-endorsed_at")
        )

        if user.is_superuser or user.is_staff:
            return endorsements
        elif user.profile.provider_profile == provider_profile:
            return endorsements
        else:
            return endorsements.filter(is_hidden=False)
    
    def get_queryset(self):
        profile_pk = self.request.query_params.get("profile_uuid")

        if profile_pk is None:
            raise ValidationError("pass user profile uuid in query params")     

        profile = get_or_none(ProviderModel, pk=profile_pk, is_active=True)
        if profile is None:
            raise ValidationError("profile not found")
        queryet = self.get_user_endorsements(profile)
        return queryet
