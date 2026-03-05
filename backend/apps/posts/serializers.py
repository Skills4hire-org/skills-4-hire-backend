from django.core.validators import validate_ipv46_address
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import Post, PostAttachment, PostTag, Comment
from ..users.provider_models import Category
from .utils.posts import  (
    validate_url, check_service_in_category,
    can_make_post, verify_post_with_amount,
    get_date
)
from .services import  create_post, CommentService
from apps.authentication.serializers import  UserReadSerializer


from django.contrib.auth import get_user_model
from django.utils.text import gettext_lazy as _
from django.db.models import Prefetch

User = get_user_model()



class PostAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = [
            "post_attachment_id",
            "post",
            "attachment_type",
            "attachmentURL",
            "created_at"
        ]
        read_only_fields = [
            "post_attachment_id", "post",
            "created_at"
        ]

    def validate_attachment_type(self, value):
        valid_types = PostAttachment.Types.values

        if value is not None and value not in valid_types:
            raise serializers.ValidationError("Invalid post media type.")
        return value

    def validate_attachmentURL(self, value):

        is_valid, url = validate_url(value)
        if not is_valid:
            raise serializers.ValidationError(_(f"{url}"))
        return  url

class PostTagSerializer(serializers.ModelSerializer):
    service = serializers.CharField(max_length=200, required=True, write_only=True)
    class Meta:
        model = PostTag
        fields = [
            "post_tag_id",
            "service",
            "service_name",
            "post",
            "created_at"
        ]

        read_only_fields = [
            "post_tag_id", "service_name",
            "post", "created_at"
        ]

        def validate_service(self, value):
            found, _ = check_service_in_category(value.strip())
            if not found:
                raise serializers.ValidationError(_("categroy  not Found"))
            return  value.title

class PostCreateSerializer(serializers.ModelSerializer):
    attachment = PostAttachmentSerializer(many=True, required=False)
    post_tag = PostTagSerializer(many=True, required=False)
    duration = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        model = Post
        fields = [
            "post_content",
            "post_type",
            "amount",
            "duration",
            "attachment",
            "post_tag"
        ]

    def validate_duration(self, value):
        if value < 1:
            raise serializers.ValidationError("Duration must be greater than or equal to 1.")
        return value

    def validate(self, attrs):
        post_type = attrs.get("post_type")
        amount = attrs.get("amount")

        # Validate post_type if model exposes allowed values
        valid_post_types = getattr(Post.PostType, "values", None)

        if valid_post_types is not None and post_type not in valid_post_types:
            raise serializers.ValidationError({"post_type": "Invalid post type."})

        request = self.context.get("request")
        user = getattr(request, "user", None)

        active_user_role = getattr(user, "active_role", None)
        if active_user_role is None:
            post_type = Post.PostType.GENERAL.value

        if not can_make_post(user_role=active_user_role, post_type=post_type):
            raise PermissionDenied()

        if not verify_post_with_amount(
            user_role=active_user_role,
            amount=amount,
            post_type=post_type
        ):
            raise PermissionDenied(detail="Couldn't verify post with amount")

        return attrs

    def create(self, validated_data):
        """Create a Post and its nested PostMedia and ServiceTag records."""

        post_attachments = validated_data.pop("attachment", [])
        post_tags = validated_data.pop("post_tag", [])

        duration = validated_data.pop("duration", None)

        request = self.context.get("request")
        user = getattr(request, "user", None)

        if duration:
             start_date, end_date = get_date(duration)
             post_instance = create_post(
                user=user,
                start_date=start_date,
                end_date=end_date,
                **validated_data
             )
        else:
            post_instance = create_post(
                user=user,
                **validated_data
            )
        # Create related PostMedia records (if any)
        if post_attachments:
            save = []
            for attachment in post_attachments:
                attachment_objs = PostAttachment(post=post_instance, **attachment)
                save.append(attachment_objs)
            PostAttachment.objects.bulk_create(save)

        # Create related PostTag records (if any)
        if post_tags:
            save = []
            for post in post_tags:
                found, category = check_service_in_category(post["service"])
                if found:
                    tag_objs = PostTag(post=post_instance, service_name=category)
                else:
                    tag_objs = PostTag(post=post_instance)
                save.append(tag_objs)
            if len(save) > 0:
                PostTag.objects.bulk_create(save)
            else:
                from asyncio.log import  logger
                logger.info("No Tags Created")
        return post_instance
    

    def update(self, instance, validated_data):
        """Update Post instance. Nested PostAttachment and PostTag are not updated here."""
        instance.post_content = validated_data.get("post_content", instance.post_content)
        instance.post_type = validated_data.get("post_type", instance.post_type)
        instance.amount = validated_data.get("amount", instance.amount)

        attachments = validated_data.pop("attachment", [])
        post_tags = validated_data.pop("post_tag", [])

        if attachments:
            attachment = instance.attachment
            for data in attachments:
                attachment.get_or_create(post=instance, **data)

        if post_tags:
            tags = instance.post_tag
            for post in post_tags:
                found, category = check_service_in_category(post["service"])
                if found:
                    tags.get_or_create(service_name=category)
                else:
                    pass

        duration = validated_data.get("duration", None)
        if duration:
            start_date, end_date = get_date(duration)
            instance.start_date = start_date
            instance.end_date = end_date
        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    user = UserReadSerializer(read_only=True)
    comment_counts = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "comment_counts",
            "post",
            "comment_id",
            "created_at",
            "updated_at",
            "is_active",
            "is_edited",
            "user",
            "message"
        ]
        read_only_fields = [
            "created_at", "is_active",
            "is_edited", "user",
            "comment_id", "user",
            "comment_counts", "post", "parent"
        ]


    def validate_message(self, value):
        value = value.strip()
        if not value or len(value) < 3:
            raise serializers.ValidationError({"message": "Comment message cannot be empty, or less than 3 chars."})
        return value

    def get_comment_counts(self, obj):
        post = Post.objects.prefetch_related(Prefetch(
            lookup="comments", queryset=Comment.active_objects.filter(post=obj.post)
        )).get(post_id=obj.post.pk)
        count = post.comments.count()
        if count == 0:
            return  0
        return count


    
    def create(self, validated_data):
        request = self.context.get("request", None)
        post = self.context.get("post")

        user = getattr(request, "user")

        try:
            comment_instance = CommentService(post=post, user=user)
            comment = comment_instance.add_comment(**validated_data)
        except Exception as e:
            raise Exception(e)
        return comment

    def update(self, instance, validated_data):
        
        instance.message = validated_data.get("message", instance.message)
        instance.save()

        return instance


class PostDetailSerializer(serializers.ModelSerializer):
    attachment = PostAttachmentSerializer(many=True, read_only=True)
    post_tag = PostTagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    user = UserReadSerializer(read_only=True)

    duration = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "user", "post_id", "post_content",
            "post_type", "amount", "is_active",
            "is_deleted", "is_pinned", "start_date",
            "end_date", "created_at", "updated_at",
            "attachment", "post_tag", "comments",
            "role", "duration"
        ]

    def get_duration(self, obj):
        start_date = obj.start_date
        end_date = obj.end_date
        if start_date is None or end_date is None:
            return None
        return  end_date - start_date


