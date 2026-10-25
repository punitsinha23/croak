"""
Django Signals for Ribbits App
Automatically trigger email notifications for certain events
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ribbit
from .email_queue import queue_new_post_broadcast


@receiver(post_save, sender=Ribbit)
def notify_followers_on_new_post(sender, instance, created, **kwargs):
    """
    Send email notifications to users when a new post is created
    
    Only triggers for:
    - New posts (not updates)
    - Original posts (not replies or reribbits)
    """
    # Only trigger for new posts, not updates
    if not created:
        return
    
    # Skip replies and reribbits - only notify for original posts
    if instance.parent or instance.is_reribbit:
        return
    
    queue_new_post_broadcast(instance)
