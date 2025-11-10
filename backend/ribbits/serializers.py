from rest_framework import serializers
from .models import Ribbit, Comment, Notification
from users.serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------- USER ----------
class MinimalUserSerializer(serializers.ModelSerializer):
    profile_pic_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "bio", "location", "profile_pic_url"]

    def get_profile_pic_url(self, obj):
        if obj.profile_pic:
            return obj.profile_pic.url
        return None


# ---------- POSTS ----------
class PostSerializer(serializers.ModelSerializer):
    author = MinimalUserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    repost = serializers.SerializerMethodField()
    reribbit_count = serializers.SerializerMethodField()
    media_url = serializers.SerializerMethodField()
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = Ribbit
        fields = [
            "id",
            "author",
            "author_email",
            "text",
            "created_at",
            "parent",
            "is_reribbit",
            "reribbit_of",
            "likes_count",
            "reply_count",
            "reribbit_count",
            "is_liked",
            "comment_count",
            "media",
            "media_url",
            "repost",
        ]
        read_only_fields = [
            "author",
            "created_at",
            "likes_count",
            "reply_count",
            "reribbit_count",
            "is_liked",
            "comment_count",
            "repost",
            "media_url",
        ]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        annotated = getattr(obj, "is_liked", None)
        if annotated is not None:
            return bool(annotated)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_repost(self, obj):
        if obj.parent:
            return PostSerializer(obj.parent, context=self.context).data
        return None

    def get_reribbit_count(self, obj):
        return Ribbit.objects.filter(parent=obj).count()

    def get_media_url(self, obj):
        if obj.media:
            return obj.media.url
        return None


class RepostSerializer(serializers.ModelSerializer):
    repost_text = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Ribbit
        fields = ["repost_text"]


# ---------- COMMENTS ----------
class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id" , "ribbit", "author", "text", "created_at"]
        read_only_fields = ["ribbit", "author", "created_at"]

    def create(self, validated_data):
        request = self.context["request"]
        ribbit_id = self.context["view"].kwargs["pk"]
        validated_data["author"] = request.user
        validated_data["ribbit"] = Ribbit.objects.get(pk=ribbit_id)
        return super().create(validated_data)


# ---------- PUBLIC USER ----------
class PublicUserSerializer(serializers.ModelSerializer):
    ribbits = PostSerializer(many=True, read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    profile_pic_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "bio",
            "location",
            "join_date",
            "ribbits",
            "profile_pic_url",
            "banner_url",
            "followers_count",
            "following_count",
            "is_following",
        ]

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_is_following(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False

    def get_profile_pic_url(self, obj):
        if obj.profile_pic:
            return obj.profile_pic.url
        return None

    def get_banner_url(self, obj):
        if obj.banner:
            return obj.banner.url
        return None
    
    def get_email(self, obj):
        return obj.email if obj.email else None


# ---------- NOTIFICATIONS ----------
class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    sender_profile_pic_url = serializers.SerializerMethodField()
    receiver_username = serializers.CharField(source="receiver.username", read_only=True)
    post_id = serializers.IntegerField(source="post.id", read_only=True)
    post = serializers.CharField(source="post.text", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "sender",
            "sender_username",
            "sender_profile_pic_url",
            "receiver",
            "receiver_username",
            "notif_type",
            "post",
            "post_id",
            "message",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "sender_username",
            "receiver_username",
            "sender_profile_pic_url",
        ]

    def get_sender_profile_pic_url(self, obj):
        if obj.sender.profile_pic:
            return obj.sender.profile_pic.url
        return None
