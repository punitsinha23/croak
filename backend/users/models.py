from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from cloudinary.models import CloudinaryField
import uuid
from datetime import timedelta


class User(AbstractUser):
    created_at = models.DateTimeField(default=timezone.now)
    bio = models.TextField(blank=True, null=True)
    profile_pic = CloudinaryField('media', folder='profiles', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    join_date = models.DateTimeField(default=timezone.now)
    following = models.ManyToManyField('self', symmetrical=False, related_name="followers", blank=True)
    banner = CloudinaryField('media', folder='banners', blank=True, null=True)

    def __str__(self):
        return self.username

class OTP(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(default=timezone.now() + timedelta(minutes=5))
    is_verfied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - {self.otp}"