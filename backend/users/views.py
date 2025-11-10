from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import random
from datetime import timedelta
import requests
from django.utils import timezone
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import OTP

User = get_user_model()

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    res = requests.post(
        "http://localhost:8081/send-otp-email", 
        json={"to": email, "otp": otp}
    )
    return res.status_code == 200


# ---------------- REGISTER ----------------
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # check if user already exists
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

        otp_code = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=5)

        # create or update OTP
        OTP.objects.update_or_create(
            email=email,
            defaults={'otp': otp_code, 'expires_at': expires_at, 'is_verfied': False}
        )

        # send email
        sent = send_otp_email(email, otp_code)
        if not sent:
            return Response({"error": "Failed to send OTP email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # temporarily store registration data in session (or frontend local storage)
        request.session[email] = serializer.validated_data
        return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)


# ---------------- VERIFY OTP ----------------
class VerifyOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_entry = OTP.objects.get(email=email)
        except OTP.DoesNotExist:
            return Response({"error": "No OTP found for this email."}, status=status.HTTP_404_NOT_FOUND)

        if otp_entry.otp != otp:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        if otp_entry.expires_at < timezone.now():
            return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

        otp_entry.is_verfied = True
        otp_entry.save()

        # create user only after OTP is verified
        user_data = request.session.get(email)
        if not user_data:
            return Response({"error": "No registration data found. Please register again."}, status=status.HTTP_400_BAD_REQUEST)
import random
import requests
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import OTP

User = get_user_model()


# ---------------- UTILITIES ----------------
def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    """Send OTP to the email using external mail service."""
    res = requests.post(
        "http://localhost:8081/send-otp-email",
        json={"to": email, "otp": otp},
    )
    return res.status_code == 200


# ---------------- REGISTER ----------------
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already registered"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_code = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=5)

        # create or update OTP entry
        OTP.objects.update_or_create(
            email=email,
            defaults={
                "otp": otp_code,
                "expires_at": expires_at,
                "is_verfied": False,
            },
        )

        # send otp
        if not send_otp_email(email, otp_code):
            return Response(
                {"error": "Failed to send OTP email."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # store registration data temporarily in cache (5 minutes)
        cache.set(email, serializer.validated_data, timeout=300)

        return Response(
            {"message": "OTP sent to your email."},
            status=status.HTTP_200_OK,
        )


# ---------------- VERIFY OTP ----------------
class VerifyOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response(
                {"error": "Email and OTP are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            otp_entry = OTP.objects.get(email=email)
        except OTP.DoesNotExist:
            return Response(
                {"error": "No OTP found for this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if otp_entry.otp != otp:
            return Response(
                {"error": "Invalid OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp_entry.expires_at < timezone.now():
            return Response(
                {"error": "OTP has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_entry.is_verfied = True
        otp_entry.save()

        # get cached user data
        user_data = cache.get(email)
        if not user_data:
            return Response(
                {"error": "No registration data found. Please register again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # create the user now that OTP is valid
        serializer = RegisterSerializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # clear the cached data
        cache.delete(email)

        return Response(
            {"message": "Email verified and account created successfully!"},
            status=status.HTTP_201_CREATED,
        )


# ---------------- LOGIN ----------------
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {"refresh": str(refresh), "access": str(refresh.access_token)}
        )


# ---------------- PROFILE ----------------
class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class listApiView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class EditProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user


# ---------------- FOLLOW / UNFOLLOW ----------------
class FollowUnfollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user
        if target_user == user:
            return Response(
                {"error": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if target_user in user.following.all():
            user.following.remove(target_user)
            return Response({"status": "unfollowed"})
        else:
            user.following.add(target_user)
            return Response(
                {
                    "status": "followed",
                    "following_count": user.following.count(),
                    "followers_count": target_user.followers.count(),
                }
            )

        serializer = RegisterSerializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.save()

        # clear session
        del request.session[email]

        return Response({"message": "Email verified and account created successfully!"}, status=status.HTTP_201_CREATED)


# ---------------- LOGIN ----------------
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


# ---------------- PROFILE VIEWS (unchanged) ----------------
class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class listApiView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class EditProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user


class FollowUnfollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        if target_user == user:
            return Response({"error": "You cannot follow yourself"}, status=status.HTTP_400_BAD_REQUEST)

        if target_user in user.following.all():
            user.following.remove(target_user)
            return Response({"status": "unfollowed"})
        else:
            user.following.add(target_user)
            return Response({
                "status": "followed",
                "following_count": user.following.count(),
                "followers_count": target_user.followers.count()
            })
