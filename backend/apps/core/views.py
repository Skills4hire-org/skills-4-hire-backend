from rest_framework import generics
from django.db.models import Q, Count
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from ..users.provider_models import ProviderModel
from ..users.profile_services.paginations import ProfilePagination
from ..users.serializers.profiles import ProviderProfilePublicSerializer
from ..posts.models import Post
from ..posts.paginations import CustomPostPagination
from ..posts.serializers.read import GeneralPostSerializer, JobPostSerializer
from .exceptions import api_response


class BaseSearch(generics.ListAPIView):

    @property
    def __optimize_provider_queryset(self):
        queryset = (
            ProviderModel.objects
                .select_related
                ('profile', 'profile__user')
                .prefetch_related
                ("services")
        )

        return queryset

    @property
    def __optimize_post_queryset(self):
        queryset = (
            Post.is_active_objects.select_related('user')
            .prefetch_related(
                'attachments', 'tags', "comments", 
                "repost_records", "likes", "user_interactions"
            )
        )
        return queryset.annotate(
            comments_counts=Count("comments", filter=Q(comments__is_active=True), distinct=True),
            likes_count=Count("likes", filter=Q(likes__is_active=True), distinct=True),
            reposts_count=Count("repost_records", filter=Q(repost_records__is_active=True), distinct=True)
        ).order_by("-created_at")

    def _providers(self, param):
        providers = self.__optimize_provider_queryset.filter(
            Q(professional_title__icontains=param) |
            Q(profile__display_name__icontains=param),
            is_active=True
        )
        paginator = ProfilePagination()

        result = None
        page = paginator.paginate_queryset(providers, self.request, self)
        serializer = ProviderProfilePublicSerializer(page, many=True, context=self.get_serializer_context())
        if page is not None:
            result = paginator.get_paginated_response(serializer.data).data
        else:
            result = serializer.data
        return result

    def _post(self, param):
        posts = self.__optimize_post_queryset.filter(
            Q(post_title__icontains=param) |
            Q(post_content__icontains=param) |
            Q(post_type__icontains=param)
        ).exclude(post_type=Post.PostType.JOB)

        result = None
        paginator = CustomPostPagination()
        page = paginator.paginate_queryset(posts, self.request, self)
        serializer = GeneralPostSerializer(page, many=True, context=self.get_serializer_context())
        if page is not None:
            result = paginator.get_paginated_response(serializer.data).data
        else:
            result = serializer.data
        return result

    def _offers(self, param):
        offers = self.__optimize_post_queryset.filter(
            Q(post_title__icontains=param) |
            Q(post_content__icontains=param) |
            Q(post_type__icontains=param),
            post_type=Post.PostType.JOB, 
        )

        result = None
        paginator = CustomPostPagination()
        page = paginator.paginate_queryset(offers, self.request, self)
        serializer = JobPostSerializer(page, many=True, context=self.get_serializer_context())
        if page is not None:
            result = paginator.get_paginated_response(serializer.data).data
        else:
            result = serializer.data
        return result
        
    @method_decorator(cache_page(60 * 10))
    def list(self, request, *args, **kwargs):
        """
        class base view set for platform searching and filtering
        """
        search_param = request.query_params.get("search")
        return api_response(
            data={
                "providers": self._providers(search_param),
                "posts": self._post(search_param),
                "offers": self._offers(search_param)
            },
            message=f"Results for '{search_param}'",
            status_code=200
        )