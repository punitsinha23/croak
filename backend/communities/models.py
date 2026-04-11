from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from cloudinary.models import CloudinaryField
from cloudinary_storage.storage import VideoMediaCloudinaryStorage

User = settings.AUTH_USER_MODEL


class Community(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    creator = models.ForeignKey(User, related_name='created_communities', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    icon = CloudinaryField('media', folder='community_icons', blank=True, null=True)
    member_count = models.PositiveIntegerField(default=1)  # Creator is first member

    class Meta:
        verbose_name_plural = "Communities"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Membership(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    ]

    user = models.ForeignKey(User, related_name='memberships', on_delete=models.CASCADE)
    community = models.ForeignKey(Community, related_name='memberships', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'community')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.community.name} ({self.role})"


class Message(models.Model):
    community = models.ForeignKey(Community, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='community_messages', on_delete=models.CASCADE)
    content = models.TextField(max_length=2000, blank=True)
    media = models.FileField(upload_to='community_vns/', blank=True, null=True, storage=VideoMediaCloudinaryStorage())
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['community', '-created_at']),
        ]

    def __str__(self):
        return f"{self.sender.username} in {self.community.name}: {self.content[:50]}"
