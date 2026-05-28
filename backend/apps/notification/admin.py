from django.contrib import admin

from .models import  Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'sender__profile__display_name', 
        "receiver__profile__display_name", 
        "content", "event", "created_at"
        ]
