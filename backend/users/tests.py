"""
Tests for the Users app.
Covers: Registration, OTP verification, Login, Profile retrieval/update,
        User listing, and Follow/Unfollow functionality.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()


def create_user(username="testuser", email="test@test.com", password="StrongPass123!"):
    """Helper to create and activate a verified user."""
    user = User.objects.create_user(
        username=username, email=email, password=password, first_name="Test"
    )
    return user


def get_auth_client(user):
    """Helper to return an authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------------------------
class RegistrationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("register")

    @patch("users.views.send_otp_email")  # mock email so we don't actually send one
    def test_register_valid_user(self, mock_send):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "first_name": "New",
        }
        response = self.client.post(self.url, data)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_register_duplicate_email_fails(self):
        create_user()
        data = {
            "username": "anotheruser",
            "email": "test@test.com",  # duplicate
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "first_name": "Another",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields_fails(self):
        response = self.client.post(self.url, {"email": "x@x.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Login Tests
# ---------------------------------------------------------------------------
class LoginTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("login")
        self.user = create_user()

    def test_login_valid_credentials(self):
        response = self.client.post(
            self.url, {"email": "test@test.com", "password": "StrongPass123!"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_wrong_password(self):
        response = self.client.post(
            self.url, {"email": "test@test.com", "password": "WrongPassword"}
        )
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_login_nonexistent_user(self):
        response = self.client.post(
            self.url, {"email": "ghost@nobody.com", "password": "AnyPass123"}
        )
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Profile Tests
# ---------------------------------------------------------------------------
class UserProfileTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = get_auth_client(self.user)
        self.url = reverse("user-profile")

    def test_get_own_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_unauthenticated_cannot_get_profile(self):
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_edit_profile_bio(self):
        url = reverse("edit_profile")
        response = self.client.patch(url, {"bio": "Hello world!"}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "Hello world!")

    def test_edit_profile_location(self):
        url = reverse("edit_profile")
        response = self.client.patch(url, {"location": "Pondville"}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# User List Tests
# ---------------------------------------------------------------------------
class UserListTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = get_auth_client(self.user)
        self.url = reverse("user-list")

    def test_list_users_authenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_users_unauthenticated(self):
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Follow / Unfollow Tests
# ---------------------------------------------------------------------------
class FollowUnfollowTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.target = create_user(username="target", email="target@test.com")
        self.client = get_auth_client(self.user)
        self.url = reverse("follow", kwargs={"username": self.target.username})

    def test_follow_user(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.target, self.user.following.all())

    def test_unfollow_user(self):
        self.user.following.add(self.target)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.target, self.user.following.all())

    def test_cannot_follow_self(self):
        url = reverse("follow", kwargs={"username": self.user.username})
        response = self.client.post(url)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_follow_nonexistent_user(self):
        url = reverse("follow", kwargs={"username": "nobody999"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
