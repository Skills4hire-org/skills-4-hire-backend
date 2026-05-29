
from django.utils import timezone
from rest_framework import serializers

from ..models import Post, PostAttachment, Comment, Repost
from .create import PostAttachmentSerializer
from ...authentication.serializers import  UserReadSerializer
from  ...users.services.serializers import ServiceCategorySerializer


class GeneralPostSerializer(serializers.ModelSerializer):
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    reposts_count = serializers.IntegerField(source='repost_records.count', read_only=True)
    attachments = PostAttachmentSerializer(many=True, read_only=True)
    tags = ServiceCategorySerializer(read_only=True, many=True)
    is_liked = serializers.SerializerMethodField()
    is_commented = serializers.SerializerMethodField()
    is_reposted = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    post_status = serializers.SerializerMethodField()

    class Meta: 
        model = Post
        fields = [
            "post_id", "post_title",
            "user", "post_content",
            "post_type", "created_at", "updated_at",
            "tags", "attachments",
            "comments_count", "likes_count", "reposts_count",
            "is_liked", "is_commented", "is_reposted", "duration", "post_status"
        ]
    
    def get_duration(self, obj):
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days
        return None
    
    def get_post_status(self, obj):
        if obj.post_type == Post.PostType.JOB:
            currrent_datetime  = timezone.now()
            if obj.end_date is None:
                return "active"
            end_datetime = obj.end_date
            if end_datetime < currrent_datetime:
                return "closed"
        return "active"
    
    
    def get_is_liked(self, obj):
        user = self.context['request'].user
        if not user or not user.is_authenticated:
            return False
        
        return obj.likes.filter(user=user).exists()
    
    def get_is_commented(self, obj):
        user = self.context['request'].user
        if not user:
            return False
        return obj.comments.filter(user=user).exists()
    
    def get_is_reposted(self, obj):
        user = self.context['request'].user
        if not user:
            return False
        return obj.repost_records.filter(reposted_by=user).exists()

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
            "is_reposted", 'user'
        ]
    

class PostDetailSerializer(GeneralPostSerializer):
    user = UserReadSerializer(read_only=True)
    class Meta(GeneralPostSerializer.Meta):
        model = GeneralPostSerializer.Meta.model
        fields = GeneralPostSerializer.Meta.fields + [
            "is_reposted", "user"   
        ]

class CommentListSerializer(serializers.ModelSerializer):

    total_replies = serializers.IntegerField(read_only=True)
    total_likes = serializers.IntegerField(read_only=True)
    attachments = PostAttachmentSerializer(read_only=True)
    user = UserReadSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_replied = serializers.SerializerMethodField()

    class Meta: 
        model = Comment
        fields = [
            "comment_id", "total_replies", "user",
            "total_likes", "message", "attachments",
            'parent', "created_at", "is_liked", "is_replied"
        ]

    def get_is_liked(self, obj):
        user = self.context['request'].user
        if not user:
            return None
        return obj.likes.filter(user=user).exists()

    def get_is_replied(self, obj):
        user = self.context['request'].user
        if not user:
            return None
        return obj.replies.filter(user=user).exists()

class RepostListSerializer(serializers.ModelSerializer):
    reposted_by = UserReadSerializer(read_only=True)
    class Meta: 
        model = Repost
        fields = [
            "repost_id", "comment", "reposted_by"
        ]