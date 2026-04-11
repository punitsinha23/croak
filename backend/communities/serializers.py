from rest_framework import serializers
from .models import Community, Membership, Message
from django.contrib.auth import get_user_model

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization"""
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'profile_pic']

    def get_profile_pic(self, obj):
        if obj.profile_pic:
            return obj.profile_pic.url
        return None


class CommunitySerializer(serializers.ModelSerializer):
    creator = UserBasicSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ['id', 'name', 'description', 'slug', 'creator', 'created_at', 
                  'icon', 'member_count', 'is_member', 'user_role']
        read_only_fields = ['slug', 'creator', 'created_at', 'member_count']

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Membership.objects.filter(user=request.user, community=obj).exists()
        return False

    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = Membership.objects.filter(user=request.user, community=obj).first()
            if membership:
                return membership.role
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'community', 'sender', 'content', 'media', 'created_at']
        read_only_fields = ['sender', 'created_at']
        extra_kwargs = {
            'content': {'required': False}
        }

    def validate(self, attrs):
        content = attrs.get('content', '')
        media = attrs.get('media', None)
        if not content and not media:
            raise serializers.ValidationError("Either content or media must be provided.")
        return attrs


class MembershipSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    community = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'user', 'community', 'role', 'joined_at']
        read_only_fields = ['joined_at']
