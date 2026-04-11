"""
Django Signals for Ribbits App
Automatically trigger email notifications for certain events
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ribbit
from .email_queue import queue_new_post_notification


@receiver(post_save, sender=Ribbit)
def notify_followers_on_new_post(sender, instance, created, **kwargs):
    """
    Send email notifications to followers when a new post is created
    
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
    
    # Get all followers of the post author
    followers = instance.author.followers.all()
    
    if followers.exists():
        # Queue email notifications to all followers
        queued_count = queue_new_post_notification(instance, followers)
        
        # Optional: log the action (useful for debugging)
        if queued_count > 0:
            print(f"Queued {queued_count} email notifications for new post by @{instance.author.username}")
