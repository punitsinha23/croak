from django.db import models
from  django.conf import settings
from django.utils import timezone
from users.models import User


User = settings.AUTH_USER_MODEL

class Ribbit(models.Model):
    author = models.ForeignKey(User , related_name='ribbits', on_delete=models.CASCADE)
    text = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now , db_index=True)

    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.SET_NULL)
    is_reribbit = models.BooleanField(default=False)
    reribbit_of = models.ForeignKey('self', null=True, blank=True, related_name='reribbit', on_delete=models.SET_NULL)

    reply_count = models.PositiveIntegerField(default=0)
    reribbit_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']


class Like(models.Model):
    ribbit = models.ForeignKey(Ribbit, related_name="likes", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="likes", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ribbit', 'user')  # prevent duplicate likes


class RibbitMedia(models.Model):
    ribbit = models.ForeignKey(Ribbit, related_name='media', on_delete=models.CASCADE) 
    file = models.URLField()       
    media_type = models.CharField(max_length=20)


class Comment(models.Model):
    ribbit = models.ForeignKey('Ribbit', related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name="comments", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)