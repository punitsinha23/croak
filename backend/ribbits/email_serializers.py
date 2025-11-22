"""
Email Preferences Serializer and ViewSet
"""
from rest_framework import serializers, viewsets, permissions
from .models import EmailPreferences


class EmailPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailPreferences
        fields = [
            'email_on_like',
            'email_on_comment',
            'email_on_follow',
            'email_on_mention',
            'email_on_reply',
            'daily_digest',
            'weekly_summary',
            'digest_time',
            'timezone',
            'email_enabled',
        ]


class EmailPreferencesViewSet(viewsets.ModelViewSet):
    """API endpoint for managing email preferences"""
    serializer_class = EmailPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own preferences
        return EmailPreferences.objects.filter(user=self.request.user)
    
    def get_object(self):
        # Get or create preferences for the current user
        prefs, created = EmailPreferences.objects.get_or_create(user=self.request.user)
        return prefs
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
