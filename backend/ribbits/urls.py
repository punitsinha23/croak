from django.urls import path
from .views import (PostApiView, RetrieveMyRibbitView, 
                    ListRibbitApiView, DeleteUpdateRibbitApiView, 
                    LikeApiView, LikedRibbitsApiView, SearchApiView,
                    CommentApiView, UserDetailApiView, NotificationListView, RepostApiView, CommentDeleteView
                    )

urlpatterns = [
    path("post/", PostApiView.as_view(), name="post"),
    path("delete/<int:pk>/", DeleteUpdateRibbitApiView.as_view(), name='delete'),
    path("update/<int:pk>/", DeleteUpdateRibbitApiView.as_view(), name='edit'),
    path("my-ribbits/", RetrieveMyRibbitView.as_view(), name="my-ribbits"),
    path("ribbits/<int:pk>/like/", LikeApiView.as_view(), name="like-ribbit"),
    path("feed/" , ListRibbitApiView.as_view(), name='feed'),
    path("liked/", LikedRibbitsApiView.as_view(), name="liked-ribbits"),
    path("ribbits/<int:pk>/comment/", CommentApiView.as_view(), name='comments'),
    path("ribbits/<int:ribbit_id>/comment/<int:comment_id>/", CommentDeleteView.as_view(), name='delete_comment'),
    path("search/", SearchApiView.as_view(), name='search'),
    path('search/<str:username>/', UserDetailApiView.as_view(), name='search-user'),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path('<int:pk>/repost/', RepostApiView.as_view(), name='repost-with-opinion'),
    ]

