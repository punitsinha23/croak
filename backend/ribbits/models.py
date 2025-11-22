from django.db import models
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model

User = settings.AUTH_USER_MODEL

class Ribbit(models.Model):
    author = models.ForeignKey(User, related_name='ribbits', on_delete=models.CASCADE)
    text = models.CharField(max_length=500, blank=True)
    media = CloudinaryField('media', folder="ribbit_media", resource_type='auto', null=True, blank=True)  
    media_type = models.CharField(max_length=20, null=True, blank=True)  
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.SET_NULL)
    is_reribbit = models.BooleanField(default=False)
    reribbit_of = models.ForeignKey('self', null=True, blank=True, related_name='reribbit', on_delete=models.SET_NULL)

    reply_count = models.PositiveIntegerField(default=0)
    reribbit_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
    
    def reribbit(self, user, text):
        repost = Ribbit.objects.create(
            author = user,
            repost_text = text,
            parent = self,
            is_reribbit = True,
            reribbit_of = self.reribbit_of or self
        )

        orignal_post = self.reribbit_of or self
        orignal_post.reribbit_count += 1
        orignal_post.save(update_fields=["reribbit_count"])
        return repost

class Like(models.Model):
    ribbit = models.ForeignKey(Ribbit, related_name="likes", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="likes", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ribbit', 'user')


class Comment(models.Model):
    ribbit = models.ForeignKey(Ribbit, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name="comments", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Reply(models.Model):
    comment = models.ForeignKey(Comment, related_name="replies", on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name="replies", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    NOTIF_TYPES = [
        ("like", "Like"),
        ("comment", "Comment"),
        ("follow", "Follow"),
        ("reribbit", "Re-ribbit"),
        ("mention", "Mention"),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES)
    post = models.ForeignKey("Ribbit", on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class EmailQueue(models.Model):
    """Queue for emails to be sent asynchronously"""
    EMAIL_TYPES = [
        ('instant', 'Instant Notification'),
        ('digest', 'Daily Digest'),
        ('weekly', 'Weekly Summary'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_queue')
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPES)
    subject = models.CharField(max_length=255)
    body_html = models.TextField()
    body_text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    priority = models.IntegerField(default=5, db_index=True)  # 1=highest, 10=lowest
    scheduled_for = models.DateTimeField(default=timezone.now, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['priority', 'scheduled_for']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['recipient', 'email_type']),
        ]
    
    def __str__(self):
        return f"{self.email_type} to {self.recipient.username} - {self.status}"


class EmailPreferences(models.Model):
    """User email notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_preferences')
    
    # Instant notifications
    email_on_like = models.BooleanField(default=True)
    email_on_comment = models.BooleanField(default=True)
    email_on_follow = models.BooleanField(default=True)
    email_on_mention = models.BooleanField(default=True)
    email_on_reply = models.BooleanField(default=True)
    
    # Digest emails
    daily_digest = models.BooleanField(default=True)
    weekly_summary = models.BooleanField(default=False)
    
    # Timing preferences
    digest_time = models.TimeField(default='09:00:00')  # 9 AM
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Master switch
    email_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Email preferences for {self.user.username}"
