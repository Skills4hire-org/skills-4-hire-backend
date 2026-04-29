from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from rest_framework import viewsets, status
from rest_framework.response import Response

from .permissions import CanAddFavourite
from .serializers import FavouriteAddSerializer, FavouriteListSerialzer, FavoriteProviderSerializer
from .models import Favourite

class FavouriteViewSet(viewsets.ModelViewSet):

    permission_classes = [CanAddFavourite]
    http_method_names = ['get', 'post', 'patch']

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return FavouriteAddSerializer
        
        if self.action in ("list", "retrieve"):
            if self.request.user.is_provider:
                return FavoriteProviderSerializer
            else:
                return FavouriteListSerialzer

    def get_queryset(self):
        user = self.request.user
        queryset = Favourite.objects\
            .select_related("owner")\
            .prefetch_related("providers")
        
        if user.is_customer:
            queryset = queryset.filter(owner=user)
        elif user.is_provider:
            queryset = queryset.filter(providers=user.profile.provider_profile)
        else:
            return queryset

        return queryset

    # @method_decorator(cache_page(60 * 2))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    

    

        


