from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password 

User = get_user_model()

class RegisterSerilizer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'bio', 'profile_pic')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password":"Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')  # remove confirmation
        password = validated_data.pop('password')  # remove and store password

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=password,  # create_user will hash it
            bio=validated_data.get('bio', ''),
            profile_pic=validated_data.get('profile_pic', None)
        )

        return user

    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True) 
    password = serializers.CharField(required=True, write_only=True)   