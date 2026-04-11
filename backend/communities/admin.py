from django.contrib import admin
from .models import Community, Membership, Message


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'creator', 'member_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'community', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__username', 'community__name']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'community', 'content_preview', 'created_at']
    list_filter = ['community', 'created_at']
    search_fields = ['sender__username', 'content']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
