"""
Django Management Command to Send Daily Reminder Emails
Run this command via cron job or scheduler to queue daily reminder emails
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from ribbits.email_queue import queue_daily_reminder
from datetime import datetime, time

User = get_user_model()


class Command(BaseCommand):
    help = 'Queue daily reminder emails for users who have them enabled'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Run in test mode (only queue for users with email starting with "test")',
        )

    def handle_self(self, *args, **options):
        test_mode = options.get('test', False)
        
        if test_mode:
            self.stdout.write(self.style.WARNING('Running in TEST mode'))
        
        # Get all users with email_enabled=True and daily_digest=True
        from ribbits.models import EmailPreferences
        
        eligible_prefs = EmailPreferences.objects.filter(
            email_enabled=True,
            daily_digest=True,
            user__email__isnull=False
        ).exclude(user__email='').select_related('user')
        
        total_users = eligible_prefs.count()
        self.stdout.write(f'Found {total_users} users with daily reminders enabled')
        
        queued_count = 0
        skipped_count = 0
        error_count = 0
        
        current_hour = timezone.now().hour
        
        for pref in eligible_prefs:
            user = pref.user
            
            # In test mode, only process test users
            if test_mode and not user.email.startswith('test'):
                continue
            
            # Check if it's time to send for this user
            # Allow +/- 1 hour window to accommodate the cron job running hourly
            user_hour = pref.digest_time.hour
            if abs(current_hour - user_hour) > 1:
                skipped_count += 1
                continue
            
            try:
                email = queue_daily_reminder(user)
                if email:
                    queued_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Queued reminder for {user.username} ({user.email})')
                    )
                else:
                    skipped_count += 1
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error queuing for {user.username}: {str(e)}')
                )
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Summary ==='))
        self.stdout.write(f'Total eligible users: {total_users}')
        self.stdout.write(self.style.SUCCESS(f'Successfully queued: {queued_count}'))
        self.stdout.write(self.style.WARNING(f'Skipped (wrong time): {skipped_count}'))
        self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
