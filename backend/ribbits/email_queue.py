"""
Email Queue Utility Functions
Handles queueing, sending, and managing email notifications
"""
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import EmailQueue, EmailPreferences, Notification
from datetime import timedelta
import requests
from django.conf import settings

User = get_user_model()


def get_user_email_prefs(user):
    """Get or create email preferences for a user"""
    prefs, created = EmailPreferences.objects.get_or_create(user=user)
    return prefs


def should_send_email(user, notification_type):
    """Check if user wants to receive this type of email"""
    prefs = get_user_email_prefs(user)
    
    if not prefs.email_enabled:
        return False
    
    type_map = {
        'like': prefs.email_on_like,
        'comment': prefs.email_on_comment,
        'follow': prefs.email_on_follow,
        'mention': prefs.email_on_mention,
        'reply': prefs.email_on_reply,
    }
    
    return type_map.get(notification_type, False)


def queue_notification_email(recipient, notification_type, context):
    """
    Queue an instant notification email
    
    Args:
        recipient: User object
        notification_type: 'like', 'comment', 'follow', 'mention', 'reply'
        context: dict with notification details (sender, post, etc.)
    """
    if not should_send_email(recipient, notification_type):
        return None
    
    # Check if user has email
    if not recipient.email:
        return None
    
    # Generate email content
    subject, html_body, text_body = generate_notification_email(notification_type, context)
    
    # Queue the email
    email = EmailQueue.objects.create(
        recipient=recipient,
        email_type='instant',
        subject=subject,
        body_html=html_body,
        body_text=text_body,
        priority=3, 
        scheduled_for=timezone.now()
    )
    
    return email


def queue_daily_digest(recipient, digest_data):
    """
    Queue a daily digest email
    
    Args:
        recipient: User object
        digest_data: dict with {
            'new_followers': int,
            'total_likes': int,
            'total_comments': int,
            'trending_posts': list,
            'suggested_users': list
        }
    """
    prefs = get_user_email_prefs(recipient)
    
    if not prefs.daily_digest or not prefs.email_enabled:
        return None
    
    if not recipient.email:
        return None
    
    # Generate digest email
    subject, html_body, text_body = generate_digest_email(digest_data, recipient)
    
    # Queue for tomorrow at user's preferred time
    scheduled_time = timezone.now().replace(
        hour=prefs.digest_time.hour,
        minute=prefs.digest_time.minute,
        second=0,
        microsecond=0
    ) + timedelta(days=1)
    
    email = EmailQueue.objects.create(
        recipient=recipient,
        email_type='digest',
        subject=subject,
        body_html=html_body,
        body_text=text_body,
        priority=5,  # Lower priority for digests
        scheduled_for=scheduled_time
    )
    
    return email


def get_pending_emails(limit=100):
    """Get pending emails ready to be sent"""
    return EmailQueue.objects.filter(
        status='pending',
        scheduled_for__lte=timezone.now(),
        retry_count__lt=3  # Max 3 retries
    ).order_by('priority', 'scheduled_for')[:limit]


def mark_email_sent(email_id):
    """Mark an email as successfully sent"""
    EmailQueue.objects.filter(id=email_id).update(
        status='sent',
        sent_at=timezone.now()
    )


def mark_email_failed(email_id, error_message):
    """Mark an email as failed and increment retry count"""
    email = EmailQueue.objects.get(id=email_id)
    email.status = 'failed' if email.retry_count >= 2 else 'pending'
    email.error_message = error_message
    email.retry_count += 1
    email.save()


def send_email_via_service(email):
    """
    Send email via FastAPI notification service
    
    Args:
        email: EmailQueue object
    """
    try:
        # Get notification service URL from settings
        service_url = getattr(settings, 'NOTIFICATIONS_SERVICE_URL', 'https://croak-notifications.vercel.app')
        
        response = requests.post(
            f"{service_url}/send-queued-email",
            json={
                "to": email.recipient.email,
                "subject": email.subject,
                "html": email.body_html,
                "text": email.body_text
            },
            timeout=10
        )
        
        if response.status_code == 200:
            mark_email_sent(email.id)
            return True
        else:
            mark_email_failed(email.id, f"Service returned {response.status_code}")
            return False
            
    except Exception as e:
        mark_email_failed(email.id, str(e))
        return False


def generate_notification_email(notification_type, context):
    """Generate email content for instant notifications"""
    from .email_templates import (
        get_like_email,
        get_comment_email,
        get_follow_email,
        get_mention_email,
        get_reply_email,
        get_new_post_from_following_email
    )
    
    templates = {
        'like': get_like_email,
        'comment': get_comment_email,
        'follow': get_follow_email,
        'mention': get_mention_email,
        'reply': get_reply_email,
        'new_post_from_following': get_new_post_from_following_email,
    }
    
    template_func = templates.get(notification_type)
    if template_func:
        return template_func(context)
    
    # Fallback
    return (
        f"New {notification_type} on Croak",
        f"<p>You have a new {notification_type}!</p>",
        f"You have a new {notification_type}!"
    )


def generate_digest_email(digest_data, recipient):
    """Generate daily digest email"""
    from .email_templates import get_daily_digest_email
    return get_daily_digest_email(digest_data, recipient)


def cleanup_old_emails(days=30):
    """Delete sent emails older than specified days"""
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count = EmailQueue.objects.filter(
        status='sent',
        sent_at__lt=cutoff_date
    ).delete()[0]
    return deleted_count


def queue_new_post_notification(post, followers):
    """
    Queue email notifications to followers when someone they follow creates a new post
    
    Args:
        post: Ribbit object (the new post)
        followers: QuerySet or list of User objects who follow the post author
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    queued_count = 0
    
    for follower in followers:
        # Check if user wants these emails
        prefs = get_user_email_prefs(follower)
        if not prefs.email_enabled or not prefs.email_on_new_post_from_following:
            continue
            
        if not follower.email:
            continue
        
        # Prepare context for email template
        context = {
            'author_name': post.author.first_name or post.author.username,
            'author_username': post.author.username,
            'post_text': post.text,
            'post_url': f'https://croak-green-shine.vercel.app/post/{post.id}',
            'has_media': bool(post.media),
            'recipient_name': follower.first_name or follower.username,
        }
        
        # Generate email content
        subject, html_body, text_body = generate_notification_email('new_post_from_following', context)
        
        # Queue the email
        EmailQueue.objects.create(
            recipient=follower,
            email_type='instant',
            subject=subject,
            body_html=html_body,
            body_text=text_body,
            priority=4,  # Medium-low priority
            scheduled_for=timezone.now()
        )
        
        queued_count += 1
    
    return queued_count


def queue_daily_reminder(recipient):
    """
    Queue a daily reminder email to encourage user to check the site
    
    Args:
        recipient: User object
    """
    prefs = get_user_email_prefs(recipient)
    
    # Check if user wants daily digest (we use same preference for reminders)
    if not prefs.daily_digest or not prefs.email_enabled:
        return None
    
    if not recipient.email:
        return None
    
    # Generate reminder email
    from .email_templates import get_daily_reminder_email
    subject, html_body, text_body = get_daily_reminder_email(recipient)
    
    # Schedule for user's preferred digest time
    scheduled_time = timezone.now().replace(
        hour=prefs.digest_time.hour,
        minute=prefs.digest_time.minute,
        second=0,
        microsecond=0
    )
    
    # If the time has passed today, schedule for tomorrow
    if scheduled_time <= timezone.now():
        scheduled_time += timedelta(days=1)
    
    email = EmailQueue.objects.create(
        recipient=recipient,
        email_type='digest',
        subject=subject,
        body_html=html_body,
        body_text=text_body,
        priority=5,  # Low priority
        scheduled_for=scheduled_time
    )
    
    return email

