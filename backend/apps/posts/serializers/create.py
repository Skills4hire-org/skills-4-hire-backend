from ...users.services.models import ServiceCategory
from ..utils.posts import  (
    validate_url,
    can_make_post, verify_post_with_amount,
    get_date
)
from ..services_T import  create_post, CommentService
from ..models import Post, PostAttachment, Comment, Repost

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ...core.utils.py import generate_thumbnails

class PostAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = [
            "post_attachment_id",
            "attachment_type",
            "attachmentURL", "public_id",
            "created_at", "thumbnail_url"
        ]
        read_only_fields = [
            "post_attachment_id",
            "created_at", "thumbnail_url"
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
    

def create_bulk_post_attachements(instance: Post = None, attachments: list[dict[str, any]] = [], comment: Comment = None):
    result = PostAttachment.objects.bulk_create(
                [
                    PostAttachment(
                        post=instance,  
                        comment=comment,
                        thumbnail_url=generate_thumbnails(data['attachmentURL']) if data['attachment_type'].upper() == PostAttachment.Types.VIDEO else None,
                        **data) 

                    for data in attachments
                ]
            )

    return result
    
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

        request = self.context.get("request")
        user = request.user
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
            create_bulk_post_attachements(post_instance, post_attachments)
        
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
            instance.attachments.delete()
            create_bulk_post_attachements(instance, attachments)
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
    attachments = PostAttachmentSerializer(many=True, required=False, default=list)
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

        attachments = validated_data.pop("attachments", None)
        try:
            comment_instance = CommentService()
            comment = comment_instance.add_comment(post=post, user=user, message=validated_data['message'])
            if attachments:
              create_bulk_post_attachements(None, attachments, comment)
        except Exception as e:
            raise Exception(e)

        return comment

    def update(self, instance, validated_data):
        instance.message = validated_data.get("message", instance.message)

        if "attachments" in validated_data:
            instance.attachments.delete()
            attachments = validated_data.pop("attachments")
            create_bulk_post_attachements(None, attachments, instance)
        return super().update(instance, validated_data)

class RepostSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Repost
        fields = [
            "comment"
        ]

    def validated_comment(self, value):

        if value and not isinstance(value, str) or len(value) < 1:
            raise serializers.ValidationError(_("Add a meaningful comment"))
        return  value.strip()

    def create(self, validated_data):
        repost = None
        user = self.context['request'].user
        post = self.context['post'] 

        if Repost.objects.filter(reposted_by=user, original_post=post).exists():
            repost = Repost.objects.get(reposted_by=user, original_post=post)
            if repost.is_active:
                raise serializers.ValidationError("You already reposted this post")
            else:
                repost.is_active = True
            repost.save(update_fields=['is_active', 'updated_at'])

        else:
            validated_data.update({
                "reposted_by": user,
                "original_post": post,
            })
            repost = super().create(validated_data)

        if not post.is_reposted:
            post.is_reposted = True
        try: 
            Post.objects.create(
                user=user, post_content=validated_data.get('comment', None), 
                post_type=post.post_type
            )
            post.save()
        except Exception as e:
            raise serializers.ValidationError(e)
        return repost

