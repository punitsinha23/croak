"""
Django management command to send daily digest emails
Run this once per day via cron job (e.g., at 9 AM)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from ribbits.models import Ribbit, Like, Comment, Notification, EmailPreferences
from ribbits.email_queue import queue_daily_digest
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate and queue daily digest emails for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Send digest to specific user (username)'
        )

    def handle(self, *args, **options):
        self.stdout.write(f"[{timezone.now()}] Starting daily digest generator...")
        
        # Get users who want daily digests
        if options.get('user'):
            users = User.objects.filter(username=options['user'])
        else:
            users = User.objects.filter(
                email_preferences__daily_digest=True,
                email_preferences__email_enabled=True
            ).exclude(email='')
        
        total_users = users.count()
        self.stdout.write(f"Generating digests for {total_users} users...")
        
        queued_count = 0
        skipped_count = 0
        
        # Yesterday's date range
        yesterday = timezone.now() - timedelta(days=1)
        yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        for user in users:
            try:
                # Get user's stats from yesterday
                digest_data = self._get_digest_data(user, yesterday_start, yesterday_end)
                
                # Only send if there's activity
                if self._has_activity(digest_data):
                    queue_daily_digest(user, digest_data)
                    queued_count += 1
                    self.stdout.write(f"  ✓ Queued digest for @{user.username}")
                else:
                    skipped_count += 1
                    self.stdout.write(f"  - Skipped @{user.username} (no activity)")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error for @{user.username}: {str(e)}"))
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"✓ Queued: {queued_count}"))
        self.stdout.write(f"- Skipped: {skipped_count} (no activity)")
        self.stdout.write(f"Total users: {total_users}")
        self.stdout.write("="*50)

    def _get_digest_data(self, user, start_date, end_date):
        """Get digest data for a user"""
        
        # New followers
        new_followers = user.followers.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).count() if hasattr(user, 'followers') else 0
        
        # Likes received
        total_likes = Like.objects.filter(
            ribbit__author=user,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).count()
        
        # Comments received
        total_comments = Comment.objects.filter(
            ribbit__author=user,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).count()
        
        # Trending posts (top 3 from yesterday)
        trending_posts = Ribbit.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).annotate(
            engagement=Count('likes') + Count('comments')
        ).order_by('-engagement')[:3]
        
        trending_posts_data = [
            {
                'author': post.author.username,
                'text': post.text,
                'likes': post.likes.count(),
                'comments': post.comments.count(),
            }
            for post in trending_posts
        ]
        
        return {
            'new_followers': new_followers,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'trending_posts': trending_posts_data,
        }

    def _has_activity(self, digest_data):
        """Check if there's any activity worth sending a digest for"""
        return (
            digest_data['new_followers'] > 0 or
            digest_data['total_likes'] > 0 or
            digest_data['total_comments'] > 0 or
            len(digest_data['trending_posts']) > 0
        )
