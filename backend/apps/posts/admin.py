from django.contrib import admin

from .models import Post, Comment, Likes, Repost, UserPostInteraction, PostAttachment

@admin.register(PostAttachment)
class PostAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'attachmentURL', "public_id", "created_at", "attachment_type", 
        "post__user__profile__display_name", "comment__user__profile__display_name"]

class PostAdmin(admin.ModelAdmin):
    list_display = ('post_id', 'user__profile__display_name', 'post_type', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('post_content',)
    list_filter = ('post_type', 'is_active', 'is_deleted')
admin.site.register(Post, PostAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment_id', 'post', 'user', "message", 'is_active', 'is_deleted', 'created_at')
    search_fields = ('message',)
    list_filter = ('is_active', 'is_deleted')
admin.site.register(Comment, CommentAdmin)

class LikesAdmin(admin.ModelAdmin):
    list_display = ('like_id', 'user', 'post', 'comment', 'is_active', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('is_active', 'created_at')
admin.site.register(Likes, LikesAdmin)

class RepostAdmin(admin.ModelAdmin):
    list_display = ('repost_id', 'original_post', 'reposted_by', 'is_active', 'created_at')
    search_fields = ('original_post__post_title',)
    list_filter = ('is_active', 'created_at')
admin.site.register(Repost, RepostAdmin)

class UserPostInteractionAdmin(admin.ModelAdmin):
    list_display = ('interaction_id', 'user', 'post', 'interaction_type', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('interaction_type', 'created_at')
admin.site.register(UserPostInteraction, UserPostInteractionAdmin)
