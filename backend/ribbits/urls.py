from django.urls import path
from .views import (PostApiView, RetrieveMyRibbitView, 
                    ListRibbitApiView, DeleteUpdateRibbitApiView, 
                    LikeApiView, LikedRibbitsApiView, SearchApiView,
                    CommentApiView, UserDetailApiView, NotificationListView, RepostApiView, CommentDeleteView, replyApiView, announce_update
                    )
from .email_serializers import EmailPreferencesViewSet
from .cron_views import process_email_queue_endpoint, send_daily_digests_endpoint, email_queue_stats

urlpatterns = [
    path("post/", PostApiView.as_view(), name="post"),
    path("delete/<int:pk>/", DeleteUpdateRibbitApiView.as_view(), name='delete'),
    path("update/<int:pk>/", DeleteUpdateRibbitApiView.as_view(), name='edit'),
    path("my-ribbits/", RetrieveMyRibbitView.as_view(), name="my-ribbits"),
    path("ribbits/<int:pk>/like/", LikeApiView.as_view(), name="like-ribbit"),
    path("feed/" , ListRibbitApiView.as_view(), name='feed'),
    path("liked/", LikedRibbitsApiView.as_view(), name="liked-ribbits"),
    path("ribbits/<int:pk>/comment/", CommentApiView.as_view(), name='comments'),
    path("comments/<int:comment_id>/replies/", replyApiView.as_view(), name="comment-replies"),
    path("ribbits/<int:ribbit_id>/comment/<int:comment_id>/", CommentDeleteView.as_view(), name='delete_comment'),
    path("search/", SearchApiView.as_view(), name='search'),
    path('search/<str:username>/', UserDetailApiView.as_view(), name='search-user'),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path('<int:pk>/repost/', RepostApiView.as_view(), name='repost-with-opinion'),
    path('announce-update/', announce_update, name='announce-update'),
    path('email-preferences/', EmailPreferencesViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='email-preferences'),
    
    # Cron endpoints
    path('cron/process-emails/', process_email_queue_endpoint, name='cron-process-emails'),
    path('cron/daily-digest/', send_daily_digests_endpoint, name='cron-daily-digest'),
    path('cron/stats/', email_queue_stats, name='cron-stats'),
    ]

