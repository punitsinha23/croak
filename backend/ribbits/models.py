from django.db import models
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model

User = settings.AUTH_USER_MODEL

class Ribbit(models.Model):
    author = models.ForeignKey(User, related_name='ribbits', on_delete=models.CASCADE)
    text = models.CharField(max_length=500, blank=True)
    media = CloudinaryField('media', folder="ribbit_media", null=True, blank=True)  
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
