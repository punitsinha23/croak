from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from .models import Like, Comment, Notification, Ribbit
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def send_email_notification(subject: str, message: str, recipient_email: str):
    """Utility function to send email notifications safely."""
    if not recipient_email:
        logger.info("No recipient email, skipping notification.")
        return

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.send(fail_silently=False)
        logger.info(f"Email sent to {recipient_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")


@receiver(post_save, sender=Like)
def like_notification(sender, instance, created, **kwargs):
    if not created:
        return

    ribbit = instance.ribbit
    sender_user = instance.user
    receiver_user = ribbit.author

    if receiver_user == sender_user:
        return

    # In-app notification
    Notification.objects.create(
        sender=sender_user,
        receiver=receiver_user,
        notif_type="like",
        post=ribbit,
        message=f"{sender_user.username} liked your ribbit."
    )

    # Email notification (fail-safe)
    subject = f"{sender_user.username} liked your ribbit!"
    message = (
        f"Hi {receiver_user.username},\n\n"
        f"{sender_user.username} liked your ribbit:\n"
        f"\"{ribbit.text[:100]}...\"\n\n"
        "Check it out on Croak!"
    )
    send_email_notification(subject, message, receiver_user.email)


@receiver(post_save, sender=Comment)
def comment_notification(sender, instance, created, **kwargs):
    if not created:
        return

    commenter = instance.author
    post_author = instance.ribbit.author

    if commenter == post_author:
        return

    # In-app notification
    Notification.objects.create(
        sender=commenter,
        receiver=post_author,
        notif_type="comment",
        post=instance.ribbit,
        message=f"{commenter.username} commented on your post."
    )

    # Email notification
    subject = f"New comment from {commenter.username}"
    message = (
        f"Hi {post_author.username},\n\n"
        f"{commenter.username} commented on your ribbit:\n"
        f"\"{instance.text[:100]}...\"\n\n"
        "Check your notifications on Croak!"
    )
    send_email_notification(subject, message, post_author.email)


@receiver(m2m_changed, sender=User.following.through)
def follow_notification(sender, instance, action, reverse, pk_set, **kwargs):
    if action != "post_add":
        return

    for pk in pk_set:
        followed_user = User.objects.get(pk=pk)
        if instance == followed_user:
            continue

        if Notification.objects.filter(
            sender=instance,
            receiver=followed_user,
            notif_type="follow"
        ).exists():
            continue

        # In-app notification
        Notification.objects.create(
            sender=instance,
            receiver=followed_user,
            notif_type="follow",
            message=f"{instance.username} started following you."
        )

        # Email notification
        subject = f"{instance.username} started following you!"
        message = (
            f"Hi {followed_user.username},\n\n"
            f"{instance.username} has just started following you on Croak.\n"
            "Visit their profile to follow back!"
        )
        send_email_notification(subject, message, followed_user.email)
