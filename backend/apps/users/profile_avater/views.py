
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Avatar
from .serializers import AvatarCreateSerializer, AvatarDetailSerializer
from ..base_model import BaseProfile
from .permissions import IsAvatarOwnerOrReadOnly


class AvatarViewSet(viewsets.ModelViewSet):

    http_method_names =  ['post', 'patch', 'delete']
    permission_classes = [IsAvatarOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ("create", "patch"):
            return AvatarCreateSerializer
        return AvatarDetailSerializer

    def get_queryset(self):
        queryset = Avatar.objects\
            .select_related("profile")\
            .filter(profile__user=self.request.user)

        if not queryset.exists():
            return Avatar.objects.none()
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user_avatar = serializer.save()
        output_serializer = AvatarDetailSerializer(user_avatar).data
        return Response(output_serializer, status=status.HTTP_201_CREATED)






    
