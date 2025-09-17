from rest_framework import serializers
from .models import Ribbit

class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    class Meta:
        model = Ribbit
        fields = ['id', 'author', 'text', 'created_at', 'parent', 
                  'is_reribbit', 'reribbit_of', 
                  'likes_count', 'reply_count', 'reribbit_count']
        read_only_fields = ['author', 'created_at', 
                            'likes_count', 'reply_count', 'reribbit_count']
