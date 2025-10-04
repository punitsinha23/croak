from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from .models import Like, Comment, Notification, Ribbit  

User = get_user_model()


def send_notification_email(subject, text_message, html_message, recipient_email):
    """Helper function to send HTML emails with plain-text fallback"""
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.attach_alternative(html_message, "text/html")
    email.send(fail_silently=False)


@receiver(post_save, sender=Like)
def like_notification(sender, instance, created, **kwargs):
    if created:
        ribbit = instance.ribbit
        if ribbit.author != instance.user:
            Notification.objects.create(
                sender=instance.user,
                receiver=ribbit.author,
                notif_type="like",
                post=ribbit,
                message=f"{instance.user.username} liked your ribbit"
            )

            subject = "New Like on Your Ribbit"
            text_msg = f"{instance.user.username} liked your ribbit: '{ribbit.content[:50]}...'"
            html_msg = f"{instance.user.username} liked your ribbit: '<b>{ribbit.content[:50]}...</b>'"
            
            send_notification_email(subject, text_msg, html_msg, ribbit.author.email)


@receiver(post_save, sender=Comment)
def comment_notification(sender, instance, created, **kwargs):
    if created:
        commenter = instance.author
        author = instance.ribbit.author
        if commenter != author:
            Notification.objects.create(
                sender=commenter,
                receiver=author,
                notif_type="comment",
                post=instance.ribbit,
                message=f"{commenter.username} commented on your post."
            )

            subject = "New Comment on Your Ribbit"
            text_msg = f"{commenter.username} commented on your ribbit: '{instance.ribbit.content[:50]}...'"
            html_msg = f"{commenter.username} commented on your ribbit: '<b>{instance.ribbit.content[:50]}...</b>'"
            
            send_notification_email(subject, text_msg, html_msg, author.email)


@receiver(m2m_changed, sender=User.following.through)
def follow_notification(sender, instance, action, reverse, pk_set, **kwargs):
    if action == "post_add":
        for pk in pk_set:
            followed_user = User.objects.get(pk=pk)
            if instance != followed_user:
                exists = Notification.objects.filter(
                    sender=instance,
                    receiver=followed_user,
                    notif_type="follow"
                ).exists()
                if not exists:
                    Notification.objects.create(
                        sender=instance,
                        receiver=followed_user,
                        notif_type="follow",
                        message=f"{instance.username} started following you."
                    )

                    subject = "New Follower on Croak"
                    text_msg = f"{instance.username} started following you. Checkout: https://croak-green-shine.vercel.app/notifications"
                    html_msg = f"""
                        <p>{instance.username} started following you.</p>
                        <p>Checkout your <a href="https://croak-green-shine.vercel.app/notifications">notifications</a>.</p>
                    """
                    send_notification_email(subject, text_msg, html_msg, followed_user.email)
