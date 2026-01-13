from django.contrib import admin

from .models import Post, Comment, PostLike

class PostAdmin(admin.ModelAdmin):
    list_display = ('post_id', 'user', 'post_type', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('post_content',)
    list_filter = ('post_type', 'is_active', 'is_deleted')
admin.site.register(Post, PostAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment_id', 'post', 'user', "message", 'is_active', 'is_deleted', 'created_at')
    search_fields = ('message',)
    list_filter = ('is_active', 'is_deleted')
admin.site.register(Comment, CommentAdmin)
