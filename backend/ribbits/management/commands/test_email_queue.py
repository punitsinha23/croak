"""
Test script for email queue system
Run this to create test emails and verify the system works
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ribbits.email_queue import queue_notification_email
from ribbits.models import EmailQueue, EmailPreferences

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the email queue system'

    def handle(self, *args, **options):
        self.stdout.write("="*60)
        self.stdout.write(self.style.SUCCESS("Email Queue System Test"))
        self.stdout.write("="*60)
        
        # Get first user
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found! Create a user first."))
            return
        
        if not user.email:
            self.stdout.write(self.style.WARNING(f"User {user.username} has no email!"))
            self.stdout.write("Setting test email...")
            user.email = f"{user.username}@example.com"
            user.save()
        
        self.stdout.write(f"\nTesting with user: {user.username} ({user.email})")
        
        # Check/create email preferences
        prefs, created = EmailPreferences.objects.get_or_create(user=user)
        if created:
            self.stdout.write(self.style.SUCCESS("✓ Created email preferences"))
        
        self.stdout.write(f"Email enabled: {prefs.email_enabled}")
        self.stdout.write(f"Email on like: {prefs.email_on_like}")
        
        # Queue a test email
        self.stdout.write("\n" + "-"*60)
        self.stdout.write("Queueing test notification email...")
        
        email = queue_notification_email(
            recipient=user,
            notification_type='like',
            context={
                'sender': 'TestUser',
                'post_text': 'This is a test post to verify the email queue system is working!',
                'post_url': 'https://croak.com/post/1',
                'recipient_name': user.first_name or user.username
            }
        )
        
        if email:
            self.stdout.write(self.style.SUCCESS(f"✓ Email queued successfully! ID: {email.id}"))
            self.stdout.write(f"  Status: {email.status}")
            self.stdout.write(f"  Priority: {email.priority}")
            self.stdout.write(f"  Subject: {email.subject}")
        else:
            self.stdout.write(self.style.WARNING("Email not queued (user preferences might be disabled)"))
        
        # Show queue stats
        self.stdout.write("\n" + "-"*60)
        self.stdout.write("Current Queue Status:")
        
        pending = EmailQueue.objects.filter(status='pending').count()
        processing = EmailQueue.objects.filter(status='processing').count()
        sent = EmailQueue.objects.filter(status='sent').count()
        failed = EmailQueue.objects.filter(status='failed').count()
        
        self.stdout.write(f"  Pending: {pending}")
        self.stdout.write(f"  Processing: {processing}")
        self.stdout.write(f"  Sent: {sent}")
        self.stdout.write(f"  Failed: {failed}")
        
        # Show recent emails
        if pending > 0:
            self.stdout.write("\n" + "-"*60)
            self.stdout.write("Recent pending emails:")
            recent = EmailQueue.objects.filter(status='pending').order_by('-created_at')[:5]
            for e in recent:
                self.stdout.write(f"  #{e.id}: {e.email_type} to {e.recipient.username} - {e.subject}")
        
        # Instructions
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("Next Steps:"))
        self.stdout.write("="*60)
        self.stdout.write("1. Run: python manage.py process_email_queue")
        self.stdout.write("2. Check if email was sent (status should change to 'sent')")
        self.stdout.write("3. Or test via API:")
        self.stdout.write(f'   curl "http://localhost:8000/api/ribbit/cron/stats/?secret=YOUR_SECRET"')
        self.stdout.write("\n")
