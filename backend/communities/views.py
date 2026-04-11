from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import F
from django.utils.dateparse import parse_datetime
from .models import Community, Membership, Message
from .serializers import CommunitySerializer, MessageSerializer, MembershipSerializer


class IsMemberPermission(permissions.BasePermission):
    """Check if user is a member of the community"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # For message creation, check community membership
        if request.method == 'POST':
            community_id = request.data.get('community')
            if community_id:
                return Membership.objects.filter(
                    user=request.user,
                    community_id=community_id
                ).exists()
        return True


class CommunityViewSet(viewsets.ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def perform_create(self, serializer):
        # Create community and automatically add creator as admin member
        community = serializer.save(creator=self.request.user)
        Membership.objects.create(
            user=self.request.user,
            community=community,
            role='admin'
        )

    def perform_update(self, serializer):
        # Only creator or admin can update
        community = self.get_object()
        membership = Membership.objects.filter(
            user=self.request.user,
            community=community
        ).first()
        
        if community.creator != self.request.user and (not membership or membership.role not in ['admin']):
            return Response(
                {'error': 'Only creator or admins can edit this community'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()

    def perform_destroy(self, instance):
        # Only creator can delete
        if instance.creator != self.request.user:
            return Response(
                {'error': 'Only the creator can delete this community'},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()

    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        """List all members of a community"""
        community = self.get_object()
        memberships = Membership.objects.filter(community=community)
        serializer = MembershipSerializer(memberships, many=True)
        return Response(serializer.data)


class MembershipViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MembershipSerializer

    @action(detail=False, methods=['post'])
    def join(self, request):
        """Join a community"""
        community_slug = request.data.get('community_slug')
        if not community_slug:
            return Response(
                {'error': 'community_slug is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        community = get_object_or_404(Community, slug=community_slug)
        
        # Check if already a member
        if Membership.objects.filter(user=request.user, community=community).exists():
            return Response(
                {'error': 'Already a member of this community'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create membership
        membership = Membership.objects.create(
            user=request.user,
            community=community,
            role='member'
        )

        # Increment member count
        Community.objects.filter(id=community.id).update(member_count=F('member_count') + 1)

        serializer = self.get_serializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def leave(self, request):
        """Leave a community"""
        community_slug = request.data.get('community_slug')
        if not community_slug:
            return Response(
                {'error': 'community_slug is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        community = get_object_or_404(Community, slug=community_slug)
        
        # Creator cannot leave
        if community.creator == request.user:
            return Response(
                {'error': 'Creator cannot leave their own community'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get membership
        membership = get_object_or_404(Membership, user=request.user, community=community)
        membership.delete()

        # Decrement member count
        Community.objects.filter(id=community.id).update(member_count=F('member_count') - 1)

        return Response({'message': 'Successfully left the community'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def remove_member(self, request):
        """Kick a member (Admin only)"""
        community_slug = request.data.get('community_slug')
        user_id = request.data.get('user_id')
        
        if not community_slug or not user_id:
            return Response(
                {'error': 'Both community_slug and user_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        community = get_object_or_404(Community, slug=community_slug)
        
        # Check if the requester is an admin
        requester_membership = get_object_or_404(Membership, user=request.user, community=community)
        if requester_membership.role != 'admin' and community.creator != request.user:
            return Response(
                {'error': 'Only admins can remove members'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if the target user is the creator
        if community.creator.id == int(user_id):
            return Response(
                {'error': 'The creator cannot be removed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get target membership
        target_membership = get_object_or_404(Membership, user_id=user_id, community=community)
        target_membership.delete()

        # Decrement member count
        Community.objects.filter(id=community.id).update(member_count=F('member_count') - 1)

        return Response({'message': 'Member removed successfully'}, status=status.HTTP_200_OK)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsMemberPermission]

    def get_queryset(self):
        """Filter messages by community and optionally by timestamp, ordered newest first."""
        queryset = Message.objects.all()
        community_slug = self.request.query_params.get('community_slug')
        if community_slug:
            queryset = queryset.filter(community__slug=community_slug)
        since = self.request.query_params.get('since')
        if since:
            try:
                since_datetime = parse_datetime(since)
                if since_datetime:
                    queryset = queryset.filter(created_at__gt=since_datetime)
            except (ValueError, TypeError):
                pass
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """Create a message and set sender to current user."""
        serializer.save(sender=self.request.user)

    def list(self, request, *args, **kwargs):
        """List messages with required community_slug parameter and membership check."""
        community_slug = request.query_params.get('community_slug')
        if not community_slug:
            return Response(
                {'error': 'community_slug query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        community = get_object_or_404(Community, slug=community_slug)
        if not Membership.objects.filter(user=request.user, community=community).exists():
            return Response(
                {'error': 'You must be a member to view messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Allow deleting a message if sender or admin"""
        message = self.get_object()
        
        # Check permissions: must be sender, or be an admin of the community
        is_sender = (message.sender_id == request.user.id)
        try:
            membership = Membership.objects.get(user=request.user, community=message.community)
            is_admin = (membership.role == 'admin' or message.community.creator_id == request.user.id)
        except Membership.DoesNotExist:
            is_admin = False

        if is_sender or is_admin:
            return super().destroy(request, *args, **kwargs)
            
        return Response(
            {'error': 'You do not have permission to delete this message'},
            status=status.HTTP_403_FORBIDDEN
        )

