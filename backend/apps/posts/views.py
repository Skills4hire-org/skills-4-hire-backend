from rest_framework import viewsets

from apps.posts.models import Post
from .serializers import PostCreateSerializer, PostDetailSerializer

class PostViewSets(viewsets.ModelViewSet):
    """
    ViewSet for managing Post instances.
    """

    def get_permissions(self):
        return super().get_permissions()
    
    
    def get_queryset(self):
        """
        Retrieve the queryset for Post instances with related media and tags.
        """
        return Post.objects.filter(
            is_active=True, is_deleted=False
        ).select_related(
            "users"
        ).prefetch_related(
            "post_media",
            "post_tags__service"
        ).all()
           

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PostCreateSerializer
        elif self.action == "list" or self.action == "retrieve":
            return PostDetailSerializer
    

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
