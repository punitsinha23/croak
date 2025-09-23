from rest_framework import serializers
from .models import Ribbit, Comment
from users.serializers import UserSerializer


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    
    class Meta:
        model = Ribbit
        fields = ['id', 'author', 'text', 'created_at', 'parent', 
                  'is_reribbit', 'reribbit_of', 
                  'likes_count', 'reply_count', 'reribbit_count', 'is_liked']
        read_only_fields = ['author', 'created_at', 
                            'likes_count', 'reply_count', 'reribbit_count', 'is_liked']
        
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

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ['ribbit', 'author', 'text', 'created_at']
        read_only_fields = ['ribbit', 'author', 'created_at']

    def create(self, validated_data):
        request = self.context["request"]
        ribbit_id = self.context["view"].kwargs["pk"]
        validated_data["author"] = request.user
        validated_data["ribbit"] = Ribbit.objects.get(pk=ribbit_id)
        return super().create(validated_data)    