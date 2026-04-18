import random
import requests
import threading
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
import os

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordSerializer,
    GoogleLoginSerializer,
)
from .models import OTP

User = get_user_model()


# ---------------- UTILITIES ----------------
def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    """Send OTP to the email using external mail service in the background."""
    def _send():
        try:
            requests.post(
                f"{os.getenv('NOTIFICATIONS_SERVICE_URL', 'https://croak-notifications.vercel.app')}/send-otp-email",
                json={"to": email, "otp": otp},
                timeout=10,
            )
        except Exception as e:
            print(f"Error sending OTP email: {e}")

    thread = threading.Thread(target=_send)
    thread.start()
    return True  # Always return True as it's now async

class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return success even if email doesn't exist for security
            return Response(
                {"message": "If an account exists with this email, an OTP has been sent."},
                status=status.HTTP_200_OK,
            )

        otp_code = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=5)

        OTP.objects.update_or_create(
            email=email,
            defaults={
                "otp": otp_code,
                "expires_at": expires_at,
                "is_verified": False,
            },
        )

        send_otp_email(email, otp_code)

        return Response(
            {"message": "If an account exists with this email, an OTP has been sent."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        password = serializer.validated_data["password"]

        try:
            otp_entry = OTP.objects.get(email=email, otp=otp, is_verified=False)
        except OTP.DoesNotExist:
            return Response(
                {"error": "Invalid OTP or email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp_entry.expires_at < timezone.now():
            return Response(
                {"error": "OTP has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update password
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()

            # Mark OTP as verified (effectively used)
            otp_entry.is_verified = True
            otp_entry.save()

            return Response(
                {"message": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User no longer exists."},
                status=status.HTTP_404_NOT_FOUND,
            )


class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["credential"]
        client_id = os.getenv("GOOGLE_CLIENT_ID")

        if not client_id:
            return Response({"error": "Google Client ID not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)

            # ID token is valid. Get the user's Google info.
            email = idinfo["email"]
            first_name = idinfo.get("given_name", "")
            # last_name = idinfo.get("family_name", "")
            # picture = idinfo.get("picture", "")

            # Check if user exists
            user, created = User.objects.get_or_create(email=email, defaults={
                "first_name": first_name,
                "is_active": True,
            })

            if created:
                # Set a random username if not provided
                base_username = email.split("@")[0]
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                user.username = username
                user.set_unusable_password()
                user.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        except ValueError:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
                "is_verified": False,
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

        otp_entry.is_verified = True
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
        user = serializer.save()

        # clear the cached data
        cache.delete(email)

        return Response(
            {
                "message": "Email verified and account created successfully!",
                "user": UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- LOGIN ----------------
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(email=email, password=password)
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
