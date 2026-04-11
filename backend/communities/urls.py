from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommunityViewSet, MembershipViewSet, MessageViewSet

# Use explicit paths to control route ordering
# Messages and membership must come before community detail routes
router = DefaultRouter()
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'membership', MembershipViewSet, basename='membership')
router.register(r'', CommunityViewSet, basename='community')

urlpatterns = [
    path('', include(router.urls)),
]
