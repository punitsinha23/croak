from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password 


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
   

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password', 'password2', 'location', 'bio', 'profile_pic',)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password":"Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')

        user = User.objects.create_user(
        username=validated_data['username'],
        first_name=validated_data['first_name'],
        email=validated_data.get('email', ''),
        password=password,
        bio=validated_data.get('bio', ''),
        profile_pic=validated_data.get('profile_pic', None),
        location=validated_data.get('location') 
        )

        return user


    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True) 
    password = serializers.CharField(required=True, write_only=True)   


class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "email", 
            "bio", "profile_pic", "location", "join_date", 
            "followers_count", "following_count", "banner"
        ]

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.email = validated_data.get('email', instance.email)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.location = validated_data.get('location', instance.location)
        if validated_data.get('profile_pic'):
            instance.profile_pic = validated_data['profile_pic']
        if 'banner' in validated_data:
            instance.banner = validated_data['banner']
        instance.save()
        return instance

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()
