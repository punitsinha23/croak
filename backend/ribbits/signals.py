from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from .models import Like, Comment, Ribbit, Notification
from django.contrib.auth import get_user_model



User = get_user_model()

@receiver(post_save, sender=Like)
def Like_notification(sender, instance, created, **kwargs):
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

@receiver(post_save, sender=Comment)
def Comment_notification(sender, instance, created, **kwargs):
    if created:
        commenter = instance.author
        author = instance.ribbit.author

        if commenter !=author:
            Notification.objects.create(
                sender=commenter,
                receiver=author,
                notif_type="comment",
                post=instance.ribbit,
                message=f"{commenter.username} commented on your post."
            )

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