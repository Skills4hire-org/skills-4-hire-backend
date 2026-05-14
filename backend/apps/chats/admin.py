from django.contrib import admin

from .models import Conversation


class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        'conversation_id',
        'participant_one',
        'participant_two',
        'room_type',
        'is_active',
        'created_at'
    )
    list_filter = ('room_type', 'is_active')
    search_fields = (
        'participant_one__username',
        'participant_two__username',
    )


admin.site.register(Conversation, ConversationAdmin)
