from django.contrib import admin

from .models import Support, SupportConversation, SupportMessage


@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    list_display = [
        'status', "customer", "admin", 
        "is_active", "created_at",
        "assigned_at", "updated_at", "resolved_at", 
        "closed_at"
        ]
    
    list_filter = ['is_active']
    search_fields = ['status', "customer__profile__display_name"]


@admin.register(SupportConversation)
class SupportConversationAdmin(admin.ModelAdmin):
    list_display = ['support__status', "created_at", "conversation_id"]

@admin.register(SupportMessage)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        "message_id", "conversation__support__status", 
        "sender", "is_staff", "message", 
        "is_read", "created_at", "updated_at"
    ]

