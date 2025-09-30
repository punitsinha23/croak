from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    join_date = models.DateTimeField(default=timezone.now)
    following = models.ManyToManyField('self', symmetrical=False, related_name="followers", blank=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    def __str__(self):
        return self.username
