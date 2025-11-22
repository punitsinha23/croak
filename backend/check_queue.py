"""Quick check of email queue status"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'croak.settings')
django.setup()

from ribbits.models import EmailQueue, EmailPreferences
from django.contrib.auth import get_user_model

User = get_user_model()

print("="*60)
print("EMAIL QUEUE STATUS")
print("="*60)

# Queue stats
pending = EmailQueue.objects.filter(status='pending').count()
sent = EmailQueue.objects.filter(status='sent').count()
failed = EmailQueue.objects.filter(status='failed').count()
total = EmailQueue.objects.count()

print(f"\n📊 Queue Statistics:")
print(f"   Pending: {pending}")
print(f"   Sent: {sent}")
print(f"   Failed: {failed}")
print(f"   Total: {total}")

# Recent emails
if total > 0:
    print(f"\n📧 Recent Emails:")
    recent = EmailQueue.objects.all().order_by('-created_at')[:5]
    for email in recent:
        print(f"   #{email.id}: [{email.status}] {email.email_type} to {email.recipient.username}")
        print(f"          Subject: {email.subject}")

# User preferences
prefs_count = EmailPreferences.objects.count()
enabled_count = EmailPreferences.objects.filter(email_enabled=True).count()

print(f"\n👤 User Preferences:")
print(f"   Total users with preferences: {prefs_count}")
print(f"   Users with email enabled: {enabled_count}")

print("\n" + "="*60)
print("✅ System is working!" if total > 0 else "⚠️  No emails in queue yet")
print("="*60)
