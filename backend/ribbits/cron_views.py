"""
Cron job endpoints for email queue processing
These endpoints should be called by scheduled jobs (GitHub Actions, platform cron, etc.)
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from ribbits.email_queue import get_pending_emails, send_email_via_service
from ribbits.models import EmailPreferences, EmailQueue
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from ribbits.models import Ribbit, Like, Comment
from ribbits.email_queue import queue_daily_digest
import os

User = get_user_model()


def verify_cron_secret(request):
    """Verify the cron secret to prevent unauthorized access"""
    secret = request.headers.get('X-Cron-Secret') or request.GET.get('secret')
    expected_secret = os.getenv('CRON_SECRET', 'your-secret-key-here')
    return secret == expected_secret


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def process_email_queue_endpoint(request):
    """
    Process pending emails in the queue
    Called by cron job every 5 minutes
    
    Usage:
    POST /api/ribbit/cron/process-emails?secret=YOUR_SECRET
    """
    if not verify_cron_secret(request):
        return Response({'error': 'Unauthorized'}, status=403)
    
    try:
        # Get pending emails
        pending_emails = get_pending_emails(limit=100)
        total = len(pending_emails)
        
        if total == 0:
            return Response({
                'status': 'success',
                'message': 'No pending emails',
                'sent': 0,
                'failed': 0
            })
        
        # Process emails
        sent_count = 0
        failed_count = 0
        
        for email in pending_emails:
            try:
                success = send_email_via_service(email)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Error sending email {email.id}: {str(e)}")
        
        return Response({
            'status': 'success',
            'total_processed': total,
            'sent': sent_count,
            'failed': failed_count,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def send_daily_digests_endpoint(request):
    """
    Generate and queue daily digest emails
    Called by cron job once per day (e.g., 9 AM)
    
    Usage:
    POST /api/ribbit/cron/daily-digest?secret=YOUR_SECRET
    """
    if not verify_cron_secret(request):
        return Response({'error': 'Unauthorized'}, status=403)
    
    try:
        # Get users who want daily digests
        users = User.objects.filter(
            email_preferences__daily_digest=True,
            email_preferences__email_enabled=True
        ).exclude(email='')
        
        total_users = users.count()
        queued_count = 0
        skipped_count = 0
        
        # Yesterday's date range
        yesterday = timezone.now() - timedelta(days=1)
        yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        for user in users:
            try:
                # Get user's stats from yesterday
                new_followers = user.followers.filter(
                    created_at__gte=yesterday_start,
                    created_at__lte=yesterday_end
                ).count() if hasattr(user, 'followers') else 0
                
                total_likes = Like.objects.filter(
                    ribbit__author=user,
                    created_at__gte=yesterday_start,
                    created_at__lte=yesterday_end
                ).count()
                
                total_comments = Comment.objects.filter(
                    ribbit__author=user,
                    created_at__gte=yesterday_start,
                    created_at__lte=yesterday_end
                ).count()
                
                # Trending posts
                trending_posts = Ribbit.objects.filter(
                    created_at__gte=yesterday_start,
                    created_at__lte=yesterday_end
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
                
                digest_data = {
                    'new_followers': new_followers,
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'trending_posts': trending_posts_data,
                }
                
                # Only send if there's activity
                if (new_followers > 0 or total_likes > 0 or total_comments > 0 or len(trending_posts_data) > 0):
                    queue_daily_digest(user, digest_data)
                    queued_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                print(f"Error for user {user.username}: {str(e)}")
        
        return Response({
            'status': 'success',
            'total_users': total_users,
            'queued': queued_count,
            'skipped': skipped_count,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def email_queue_stats(request):
    """
    Get email queue statistics
    
    Usage:
    GET /api/ribbit/cron/stats?secret=YOUR_SECRET
    """
    if not verify_cron_secret(request):
        return Response({'error': 'Unauthorized'}, status=403)
    
    try:
        pending = EmailQueue.objects.filter(status='pending').count()
        processing = EmailQueue.objects.filter(status='processing').count()
        failed = EmailQueue.objects.filter(status='failed').count()
        
        # Sent today
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sent_today = EmailQueue.objects.filter(
            status='sent',
            sent_at__gte=today
        ).count()
        
        return Response({
            'pending': pending,
            'processing': processing,
            'failed': failed,
            'sent_today': sent_today,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)
