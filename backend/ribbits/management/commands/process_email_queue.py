"""
Django management command to process the email queue
Run this every 5 minutes via cron job
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from ribbits.email_queue import get_pending_emails, send_email_via_service
import time


class Command(BaseCommand):
    help = 'Process pending emails in the queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of emails to process in one run'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='Delay between emails in seconds (to avoid rate limiting)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        delay = options['delay']
        
        self.stdout.write(f"[{timezone.now()}] Starting email queue processor...")
        
        # Get pending emails
        pending_emails = get_pending_emails(limit=limit)
        total = len(pending_emails)
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS("No pending emails to process."))
            return
        
        self.stdout.write(f"Found {total} pending emails to process.")
        
        # Process each email
        sent_count = 0
        failed_count = 0
        
        for email in pending_emails:
            try:
                self.stdout.write(f"Sending {email.email_type} email to {email.recipient.email}...")
                
                success = send_email_via_service(email)
                
                if success:
                    sent_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Sent successfully"))
                else:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ Failed to send"))
                
                # Delay to avoid rate limiting
                if delay > 0:
                    time.sleep(delay)
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"✓ Sent: {sent_count}"))
        self.stdout.write(self.style.ERROR(f"✗ Failed: {failed_count}"))
        self.stdout.write(f"Total processed: {sent_count + failed_count}/{total}")
        self.stdout.write("="*50)
