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
            if getattr(self.request.user, "is_provider", False):
                return FavoriteProviderSerializer
            return FavouriteListSerialzer

        return FavouriteListSerialzer

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False) or not getattr(user, "is_authenticated", False):
            return Favourite.objects.none()

        queryset = Favourite.objects\
            .select_related("owner")\
            .prefetch_related("providers")
        
        if getattr(user, "is_customer", False):
            queryset = queryset.filter(owner=user)
        elif getattr(user, "is_provider", False):
            provider_profile = getattr(user.profile, "provider_profile", None)
            if provider_profile is None:
                return Favourite.objects.none()
            queryset = queryset.filter(providers=provider_profile)
        else:
            return Favourite.objects.none()

        return queryset

    # @method_decorator(cache_page(60 * 2))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    

    

        


