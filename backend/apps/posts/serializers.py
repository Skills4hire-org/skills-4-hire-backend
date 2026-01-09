from rest_framework import serializers
from .models import Post, PostMedia, ServiceTag, SkillCategory
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = [
            "postmedia_id",
            "post_media_type",
            "post_media_uri"
        ]

    def validate_post_media_type(self, value):
        try:
            valid_values = getattr(PostMedia.PostMediaTypes, "values")
        except Exception:
            valid_values = None

        if valid_values is not None and value not in valid_values:
            raise serializers.ValidationError("Invalid post media type.")

        return value
    
class ServiceTagSerializer(serializers.ModelSerializer):
    # Accept service as a primary key and validate against SkillCategory queryset
    service = serializers.PrimaryKeyRelatedField(queryset=SkillCategory.objects.all())

    class Meta:
        model = ServiceTag
        fields = [
            "service_tag_id",
            "service"
        ]
    

class PostCreateSerializer(serializers.ModelSerializer):
    post_media = PostMediaSerializer(many=True, required=False)
    post_tag = ServiceTagSerializer(many=True, required=False)
    duration = serializers.IntegerField(min_value=1)

    class Meta:
        model = Post
        fields = [
            "post_content",
            "post_type",
            "amount",
            "duration",
            "post_media",
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
        if user is None:
            raise serializers.ValidationError("Authenticated user is required to create a post.")

        allowed_services = {
            "providers": [Post.PostType.GENERAL, Post.PostType.SERVICE, Post.PostType.QUESTION],
            "client": [Post.PostType.GENERAL, Post.PostType.JOB, Post.PostType.QUESTION],
        }

        if getattr(user, "active_role", None) == User.RoleChoices.SERVICE_PROVIDER and post_type not in allowed_services["providers"]:
            raise serializers.ValidationError({"post_type": f"Post privileges for providers: {allowed_services['providers']}"})

        if getattr(user, "active_role", None) == User.RoleChoices.CLIENT and post_type not in allowed_services["client"]:
            raise serializers.ValidationError({"post_type": f"Post privileges for clients: {allowed_services['client']}"})

        if amount is not None and getattr(user, "active_role", None) != User.RoleChoices.CLIENT:
            raise serializers.ValidationError({"amount": "Only users with the client role may set `amount`."})

        if post_type == Post.PostType.JOB and not amount:
            raise serializers.ValidationError({"amount": "Job posts require an `amount`."})

        if post_type != Post.PostType.JOB and amount:
            raise serializers.ValidationError({"amount": "Only job posts may include an `amount`."})

        return attrs
    

    def create(self, validated_data):
        """Create a Post and its nested PostMedia and ServiceTag records."""

        post_media = validated_data.pop("post_media", [])
        post_tags = validated_data.pop("post_tag", [])

        duration = validated_data.pop("duration", None)

        start_date = timezone.now()
        end_date = start_date + timezone.timedelta(days=duration) if duration else None

        request = self.context.get("request")
        user = getattr(request, "user", None)

        # Create and save the Post instance first so related FKs can reference it
        post_instance = Post.objects.create(user=user, start_date=start_date, end_date=end_date, **validated_data)

        # Create related PostMedia records (if any)
        if post_media:
            media_objs = [PostMedia(post=post_instance, **data) for data in post_media]
            PostMedia.objects.bulk_create(media_objs)

        # Create related ServiceTag records (if any)
        if post_tags:
            tag_objs = [ServiceTag(post=post_instance, **data) for data in post_tags]
            ServiceTag.objects.bulk_create(tag_objs)

        return post_instance
    

    def update(self, instance, validated_data):
        """Update Post instance. Nested PostMedia and ServiceTag are not updated here."""
        instance.post_content = validated_data.get("post_content", instance.post_content)
        instance.post_type = validated_data.get("post_type", instance.post_type)
        instance.amount = validated_data.get("amount", instance.amount)

        duration = validated_data.get("duration", None)
        if duration:
            instance.end_date = instance.start_date + timezone.timedelta(days=duration)

        instance.save()
        return instance


class PostDetailSerializer(serializers.ModelSerializer):
    post_media = PostMediaSerializer(many=True, read_only=True)
    post_tag = ServiceTagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            "post_id",
            "post_content",
            "post_type",
            "amount",
            "is_active",
            "is_deleted",
            "is_pinned",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
            "post_media",
            "post_tag"
        ]

