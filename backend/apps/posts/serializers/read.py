
from rest_framework import serializers

from ..models import Post, PostAttachment, Comment
from .create import PostAttachmentSerializer
from ...authentication.serializers import  UserReadSerializer
from  ...users.services.serializers import ServiceCategorySerializer


class GeneralPostSerializer(serializers.ModelSerializer):
    comments_counts = serializers.IntegerField(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    reposts_count = serializers.IntegerField(read_only=True)
    attachments = PostAttachmentSerializer(many=True, read_only=True)
    tags = ServiceCategorySerializer(read_only=True, many=True)

    class Meta: 
        model = Post
        fields = [
            "post_id", "post_title",
            "user", "post_content",
            "post_type", "created_at", "updated_at",
            "tags", "attachments",
            "comments_counts", "likes_count", "reposts_count"
        ]

class ServicePostSerializer(GeneralPostSerializer):

    class Meta(GeneralPostSerializer.Meta):
        model = GeneralPostSerializer.Meta.model
        fields = GeneralPostSerializer.Meta.fields

class JobPostSerializer(GeneralPostSerializer):

    user = UserReadSerializer(read_only=True)
    class Meta(GeneralPostSerializer.Meta):
        model = GeneralPostSerializer.Meta.model
        fields = GeneralPostSerializer.Meta.fields + [
            "amount", "start_date", "end_date", "is_remote", 
            "country", "city", "state",
            "is_reposted", "reposted_at", 'user'
        ]

class PostDetailSerializer(GeneralPostSerializer):
    user = UserReadSerializer(read_only=True)

    class Meta(GeneralPostSerializer.Meta):
        model = GeneralPostSerializer.Meta.model
        fields = GeneralPostSerializer.Meta.fields + [
            "is_reposted", "reposted_at", "user"
        ]

class CommentListSerializer(serializers.ModelSerializer):

    class Meta: 
        model = Comment
        fields = [""]

class RepostListSerializer(serializers.ModelSerializer):
    parent = GeneralPostSerializer(read_only=True)
    comments_counts = serializers.IntegerField(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    reposts_count = serializers.IntegerField(read_only=True)

    class Meta: 
        model = Post
        fields = [
            "post_id", "repost_quote", 
            "parent", "comments_counts", "likes_count",
            "reposts_count", "reposted_at", 
        ]