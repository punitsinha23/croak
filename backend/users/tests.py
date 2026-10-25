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


class OtpVerificationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.data = {
            "username": "otpuser",
            "email": "otp@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "first_name": "Otp",
        }

    @patch("users.views.send_otp_email")
    def register(self, mock_send):
        self.client.post(reverse("register"), self.data)
        return mock_send.call_args[0][1]

    def test_register_does_not_create_user_before_verification(self):
        self.register()
        self.assertFalse(User.objects.filter(email="otp@example.com").exists())

    def test_verify_with_correct_otp_creates_user(self):
        otp = self.register()
        response = self.client.post(reverse("verify_otp"), {"email": "otp@example.com", "otp": otp})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="otp@example.com")
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_verify_with_wrong_otp_fails(self):
        otp = self.register()
        wrong = "000000" if otp != "000000" else "111111"
        response = self.client.post(reverse("verify_otp"), {"email": "otp@example.com", "otp": wrong})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="otp@example.com").exists())

    def test_verify_with_expired_otp_fails(self):
        from datetime import timedelta
        from django.utils import timezone
        from .models import OTP
        otp = self.register()
        OTP.objects.filter(email="otp@example.com").update(expires_at=timezone.now() - timedelta(seconds=1))
        response = self.client.post(reverse("verify_otp"), {"email": "otp@example.com", "otp": otp})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="otp@example.com").exists())

    def test_verification_logs_the_user_in(self):
        from rest_framework_simplejwt.tokens import AccessToken
        otp = self.register()
        response = self.client.post(reverse("verify_otp"), {"email": "otp@example.com", "otp": otp})
        user = User.objects.get(email="otp@example.com")
        self.assertEqual(AccessToken(response.data["access"])["user_id"], str(user.pk))
        self.assertIn("refresh", response.data)

    def test_pending_signup_survives_cache_loss(self):
        from django.core.cache import cache
        otp = self.register()
        cache.clear()
        response = self.client.post(reverse("verify_otp"), {"email": "otp@example.com", "otp": otp})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_pending_signup_stores_hashed_password(self):
        from .models import PendingSignup
        self.register()
        pending = PendingSignup.objects.get(email="otp@example.com")
        self.assertNotIn("StrongPass123!", pending.password)

    def test_pending_signup_removed_after_verification(self):
        from .models import PendingSignup
        otp = self.register()
        self.client.post(reverse("verify_otp"), {"email": "otp@example.com", "otp": otp})
        self.assertFalse(PendingSignup.objects.exists())

    def test_registering_again_replaces_pending_signup(self):
        from .models import PendingSignup
        self.register()
        self.data["first_name"] = "Changed"
        otp = self.register()
        self.assertEqual(PendingSignup.objects.count(), 1)
        self.client.post(reverse("verify_otp"), {"email": "otp@example.com", "otp": otp})
        self.assertEqual(User.objects.get(email="otp@example.com").first_name, "Changed")

    def test_username_taken_before_verification_fails_cleanly(self):
        otp = self.register()
        create_user(username="otpuser", email="someoneelse@test.com")
        response = self.client.post(reverse("verify_otp"), {"email": "otp@example.com", "otp": otp})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="otp@example.com").exists())

    def test_blank_username_is_generated_from_email(self):
        self.data["username"] = ""
        otp = self.register()
        self.client.post(reverse("verify_otp"), {"email": "otp@example.com", "otp": otp})
        self.assertEqual(User.objects.get(email="otp@example.com").username, "otp")

    def test_verify_unknown_email_returns_404(self):
        response = self.client.post(reverse("verify_otp"), {"email": "nobody@example.com", "otp": "123456"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_verify_requires_email_and_otp(self):
        response = self.client.post(reverse("verify_otp"), {"email": "otp@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="reset@test.com")

    @patch("users.views.send_otp_email")
    def request_reset(self, email, mock_send):
        response = self.client.post(reverse("password_reset_request"), {"email": email})
        otp = mock_send.call_args[0][1] if mock_send.called else None
        return response, otp

    def confirm(self, otp, password="BrandNewPass456!"):
        return self.client.post(reverse("password_reset_confirm"), {
            "email": "reset@test.com", "otp": otp, "password": password, "password2": password,
        })

    def test_request_for_unknown_email_gives_same_response(self):
        known, _ = self.request_reset("reset@test.com")
        unknown, otp = self.request_reset("ghost@test.com")
        self.assertEqual(unknown.status_code, status.HTTP_200_OK)
        self.assertEqual(known.data, unknown.data)
        self.assertIsNone(otp)

    def test_reset_with_valid_otp_changes_password(self):
        _, otp = self.request_reset("reset@test.com")
        response = self.confirm(otp)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewPass456!"))

    def test_reset_with_wrong_otp_fails(self):
        _, otp = self.request_reset("reset@test.com")
        response = self.confirm("000000" if otp != "000000" else "111111")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("StrongPass123!"))

    def test_otp_cannot_be_reused(self):
        _, otp = self.request_reset("reset@test.com")
        self.confirm(otp)
        response = self.confirm(otp, password="AnotherPass789!")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test-client-id"})
class GoogleLoginTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("google_login")

    @patch("users.views.id_token.verify_oauth2_token")
    def test_new_google_user_is_created_with_tokens(self, mock_verify):
        mock_verify.return_value = {"email": "gfrog@gmail.com", "given_name": "Gee"}
        response = self.client.post(self.url, {"credential": "fake-token"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        user = User.objects.get(email="gfrog@gmail.com")
        self.assertEqual(user.username, "gfrog")
        self.assertFalse(user.has_usable_password())

    @patch("users.views.id_token.verify_oauth2_token")
    def test_username_collision_gets_suffix(self, mock_verify):
        create_user(username="gfrog", email="other@test.com")
        mock_verify.return_value = {"email": "gfrog@gmail.com", "given_name": "Gee"}
        self.client.post(self.url, {"credential": "fake-token"})
        self.assertEqual(User.objects.get(email="gfrog@gmail.com").username, "gfrog1")

    @patch("users.views.id_token.verify_oauth2_token")
    def test_existing_user_logs_in_without_duplicate(self, mock_verify):
        create_user(username="existing", email="exists@gmail.com")
        mock_verify.return_value = {"email": "exists@gmail.com"}
        response = self.client.post(self.url, {"credential": "fake-token"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.filter(email="exists@gmail.com").count(), 1)

    @patch("users.views.id_token.verify_oauth2_token", side_effect=ValueError("bad token"))
    def test_invalid_google_token_rejected(self, mock_verify):
        response = self.client.post(self.url, {"credential": "forged"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    @patch.dict("os.environ", {"GOOGLE_CLIENT_ID": ""})
    def test_missing_client_id_returns_500(self):
        response = self.client.post(self.url, {"credential": "anything"})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class FastLoginTests(TestCase):

    def test_login_response_includes_profile(self):
        create_user(username="speedy", email="speedy@test.com")
        response = APIClient().post(reverse("login"), {"email": "speedy@test.com", "password": "StrongPass123!"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "speedy")
        self.assertIn("access", response.data)

    def test_health_endpoint_is_public_and_skips_the_database(self):
        with self.assertNumQueries(0):
            response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class TokenLifetimeTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        create_user(email="stay@test.com")

    def login(self):
        return self.client.post(reverse("login"), {"email": "stay@test.com", "password": "StrongPass123!"})

    def test_refresh_token_lasts_thirty_days(self):
        from datetime import timedelta
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken(self.login().data["refresh"])
        lifetime = token["exp"] - token["iat"]
        self.assertEqual(lifetime, int(timedelta(days=30).total_seconds()))

    def test_refreshing_issues_a_new_refresh_token(self):
        refresh = self.login().data["refresh"]
        response = self.client.post(reverse("token_refresh"), {"refresh": refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertNotEqual(response.data["refresh"], refresh)
