from django.urls import path
from .views import (PostApiView, RetrieveMyRibbitView, 
                    ListRibbitApiView, DeleteUpdateRibbitApiView, 
                    LikeApiView, LikedRibbitsApiView, SearchApiView,
                    CommentApiView
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
    path("search/", SearchApiView.as_view(), name='search')

    ]

