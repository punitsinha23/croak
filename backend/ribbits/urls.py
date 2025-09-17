from django.urls import path
from .views import PostApiView, RetrieveMyRibbitView, ListRibbitApiView, DeleteUpdateRibbitApiView

urlpatterns = [
    path("post/", PostApiView.as_view(), name="post"),
    path("delete/<int:pk>/", DeleteUpdateRibbitApiView.as_view(), name='delete'),
     path("update/<int:pk>/", DeleteUpdateRibbitApiView.as_view(), name='edit'),
    path("my-ribbits/", RetrieveMyRibbitView.as_view(), name="my-ribbits"),
    path("feed/" , ListRibbitApiView.as_view(), name='feed')
    ]

