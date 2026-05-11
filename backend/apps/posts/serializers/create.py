from ...users.services.models import ServiceCategory
from ..utils.posts import  (
    validate_url,
    can_make_post, verify_post_with_amount,
    get_date
)
from ..services import  create_post, CommentService
from ..models import Post, PostAttachment, Comment

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
    
    def create(self, validated_data):
        return None
    
    def update(self, instance, validated_data):
        return None
    
class PostCreateSerializer(serializers.ModelSerializer):
    attachments = PostAttachmentSerializer(many=True, required=False)
    duration = serializers.IntegerField(min_value=1, required=False)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ServiceCategory.objects.all(),
        required=False
    )

    class Meta:
        model = Post
        fields = [
            "post_title", "post_content",
            "post_type", "amount",
            "duration", "attachments",
            "tags", "country", "state", "city",
            "is_remote",
        ]

    def validate_duration(self, value):
        if value < 1:
            raise serializers.ValidationError("Duration must be greater than or equal to 1.")
        return value

    def validate(self, attrs):
        post_type = attrs.get("post_type")
        amount = attrs.get("amount", None)
        user = self.context['request'].user

        if post_type == Post.PostType.SERVICE.value and not user.is_provider:
            raise PermissionDenied(detail="Only providers can create service posts.")
        
        if post_type == Post.PostType.JOB.value and not user.is_customer:
            raise PermissionDenied(detail="Only customers can create job posts.")

        # Validate post_type if model exposes allowed values
        valid_post_types = getattr(Post.PostType, "values", None)

        if valid_post_types is not None and post_type not in valid_post_types:
            raise serializers.ValidationError({"post_type": "Invalid post type."})

        user = self.context['request'].user
        if not can_make_post(user=user, post_type=post_type):
            raise PermissionDenied()

        if not verify_post_with_amount(
            user=user,
            amount=amount,
            post_type=post_type
        ):
            raise PermissionDenied(detail="Couldn't verify job post")

        return attrs

    def create(self, validated_data):
        """Create a Post and its nested PostMedia and ServiceTag records."""

        post_attachments = validated_data.pop("attachments", [])
        duration = validated_data.pop("duration", None)
        tags = validated_data.pop("tags", [])

        user = self.context['request'].user

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
            PostAttachment.objects.bulk_create(
                [PostAttachment(post=post_instance, **data) for data in post_attachments]
            )
        
        if tags:
            post_instance.tags.set(tags)

        return post_instance

    def update(self, instance, validated_data):
        """Update Post instance. Nested PostAttachment and PostTag are not updated here."""
        instance.post_content = validated_data.get("post_content", instance.post_content)
        instance.post_type = validated_data.get("post_type", instance.post_type)
        instance.amount = validated_data.get("amount", instance.amount)

        attachments = validated_data.pop("attachment", [])
        tags = validated_data.pop("tags", [])

        if attachments:
            attachment = instance.attachment
            for data in attachments:
                attachment.get_or_create(post=instance, **data)

        if tags:
            instance.tags.set(tags)

        duration = validated_data.pop("duration", None)
        if duration:
            start_date, end_date = get_date(duration)
            instance.start_date = start_date
            instance.end_date = end_date

        instance.save()

        super().update(instance, validated_data)
        return instance

class CommentCreateSerializer(serializers.ModelSerializer):
    attachments = PostAttachmentSerializer(many=True, required=False)
    class Meta:
        model = Comment
        fields = [
            "message", "attachments"
        ]

    def validate_message(self, value):
        value = value.strip()
        if not value or len(value) < 1:
            raise serializers.ValidationError({"message": "Comment message cannot be empty, or less than 3 chars."})
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        post = self.context.get("post")

        attachments = validated_data.pop("attachments")

        try:
            comment_instance = CommentService(post=post, user=user)
            comment = comment_instance.add_comment(**validated_data)

            if attachments:
                PostAttachment.objects.bulk_create([
                    PostAttachment(comment=comment, **data)
                    for data in attachments
                ])
        except Exception as e:
            raise Exception(e)

        return comment

    def update(self, instance, validated_data):
        instance.message = validated_data.get("message", instance.message)

        if "attachments" in validated_data:
            instance_attachment = instance.attachment.all().delete()
            PostAttachment.objects.bulk_create([
                PostAttachment(comment=instance, **data)
                for data in validated_data['attachments']
            ])

        validated_data.pop("attachments")
        super().update(instance, validated_data)
    
        return instance
    
class RepostSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Post
        fields = [
            "repost_quote"
        ]

    def validated_repost_quote(self, value):

        if value and not isinstance(value, str) or len(value) < 3:
            raise serializers.ValidationError(_("Your repost quote is Invalid"))
        return  value.strip()

    def create(self, validated_data):

        user = self.context['request'].user
        post = self.context['post'] 

        if Post.is_active_objects.filter(user=user, parent=post).exists():
            raise serializers.ValidationError("You already reposted this post")
        
        if not post.is_reposted:
            post.is_reposted = True
        try:
            validated_data.update({
                "user": user,
                "parent": post,
                "reposted_at": timezone.now()
            })
        
            repost = super().create(validated_data)
            post.save()
        except Exception as e:
            raise serializers.ValidationError(e)
        return repost

