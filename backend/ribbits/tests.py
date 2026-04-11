"""
Tests for the Ribbits app.
Covers: Post creation/deletion, Feed, Likes, Comments, Reposts,
        Search, Notifications.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Ribbit, Like, Comment, Notification

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def create_user(username="ribbituser", email="ribbit@test.com", password="Pass1234!"):
    return User.objects.create_user(
        username=username, email=email, password=password, first_name="Ribbit"
    )


def get_auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def create_ribbit(user, text="Hello pond!"):
    return Ribbit.objects.create(author=user, text=text)


# ---------------------------------------------------------------------------
# Post (Ribbit) Creation Tests
# ---------------------------------------------------------------------------
class PostCreationTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = get_auth_client(self.user)
        self.url = reverse("post")

    def test_create_ribbit_success(self):
        response = self.client.post(self.url, {"text": "My first ribbit!"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ribbit.objects.count(), 1)

    def test_create_empty_ribbit_fails(self):
        """A ribbit with no text and no media should be rejected."""
        response = self.client.post(self.url, {"text": ""})
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_cannot_post(self):
        client = APIClient()
        response = client.post(self.url, {"text": "Ghost ribbit"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ribbit_text_too_long(self):
        """Text longer than 500 characters should be rejected."""
        response = self.client.post(self.url, {"text": "x" * 501})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Ribbit Deletion Tests
# ---------------------------------------------------------------------------
class RibbitDeletionTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.other = create_user(username="other", email="other@test.com")
        self.ribbit = create_ribbit(self.user)
        self.client = get_auth_client(self.user)

    def test_owner_can_delete_ribbit(self):
        url = reverse("delete", kwargs={"pk": self.ribbit.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Ribbit.objects.count(), 0)

    def test_non_owner_cannot_delete_ribbit(self):
        client = get_auth_client(self.other)
        url = reverse("delete", kwargs={"pk": self.ribbit.pk})
        response = client.delete(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.assertEqual(Ribbit.objects.count(), 1)

    def test_delete_nonexistent_ribbit(self):
        url = reverse("delete", kwargs={"pk": 99999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Feed Tests
# ---------------------------------------------------------------------------
class FeedTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.followed = create_user(username="followed", email="followed@test.com")
        self.user.following.add(self.followed)
        self.client = get_auth_client(self.user)
        self.url = reverse("feed")

    def test_feed_contains_followed_user_ribbits(self):
        create_ribbit(self.followed, "From followed user")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        texts = [r["text"] for r in (response.data.get("results") if "results" in response.data else response.data)]
        self.assertIn("From followed user", texts)

    def test_feed_includes_unfollowed_ribbit(self):
        stranger = create_user(username="stranger", email="stranger@test.com")
        create_ribbit(stranger, "From stranger")
        response = self.client.get(self.url)
        texts = [r["text"] for r in (response.data.get("results") if "results" in response.data else response.data)]
        self.assertIn("From stranger", texts)

    def test_unauthenticated_can_see_feed(self):
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# My Ribbits Tests
# ---------------------------------------------------------------------------
class MyRibbitsTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = get_auth_client(self.user)
        self.url = reverse("my-ribbits")

    def test_returns_only_own_ribbits(self):
        create_ribbit(self.user, "Mine!")
        other = create_user(username="other2", email="other2@test.com")
        create_ribbit(other, "Not mine!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results") if "results" in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "Mine!")


# ---------------------------------------------------------------------------
# Like Tests
# ---------------------------------------------------------------------------
class LikeTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.other = create_user(username="liker", email="liker@test.com")
        self.ribbit = create_ribbit(self.user)
        self.client = get_auth_client(self.other)
        self.url = reverse("like-ribbit", kwargs={"pk": self.ribbit.pk})

    def test_like_ribbit(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Like.objects.count(), 1)

    def test_unlike_ribbit(self):
        Like.objects.create(ribbit=self.ribbit, user=self.other)
        response = self.client.post(self.url)  # Toggle off
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Like.objects.count(), 0)

    def test_unauthenticated_cannot_like(self):
        client = APIClient()
        response = client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_like_nonexistent_ribbit(self):
        url = reverse("like-ribbit", kwargs={"pk": 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Comment Tests
# ---------------------------------------------------------------------------
class CommentTests(TestCase):

    def setUp(self):
        self.author = create_user()
        self.commenter = create_user(username="commenter", email="commenter@test.com")
        self.ribbit = create_ribbit(self.author)
        self.client = get_auth_client(self.commenter)
        self.url = reverse("comments", kwargs={"pk": self.ribbit.pk})

    def test_add_comment(self):
        response = self.client.post(self.url, {"text": "Nice ribbit!"})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(Comment.objects.count(), 1)

    def test_get_comments(self):
        Comment.objects.create(ribbit=self.ribbit, author=self.commenter, text="Hi!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty_comment_fails(self):
        response = self.client.post(self.url, {"text": ""})
        self.assertNotIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_delete_own_comment(self):
        comment = Comment.objects.create(ribbit=self.ribbit, author=self.commenter, text="Delete me")
        url = reverse("delete_comment", kwargs={"ribbit_id": self.ribbit.pk, "comment_id": comment.pk})
        response = self.client.delete(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        self.assertEqual(Comment.objects.count(), 0)


# ---------------------------------------------------------------------------
# Search Tests
# ---------------------------------------------------------------------------
class SearchTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = get_auth_client(self.user)
        self.url = reverse("search")

    def test_search_ribbit_by_text(self):
        create_ribbit(self.user, "Unique pond phrase")
        response = self.client.get(self.url, {"q": "Unique pond phrase"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_user_by_username(self):
        response = self.client.get(self.url, {"q": "ribbituser"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty_search_returns_results(self):
        response = self.client.get(self.url, {"q": ""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_search(self):
        client = APIClient()
        response = client.get(self.url, {"q": "test"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# User Detail (Public profile) Tests
# ---------------------------------------------------------------------------
class UserDetailTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = get_auth_client(self.user)

    def test_get_existing_user_profile(self):
        url = reverse("search-user", kwargs={"username": self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)

    def test_get_nonexistent_user_profile(self):
        url = reverse("search-user", kwargs={"username": "nobody9999"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Repost Tests
# ---------------------------------------------------------------------------
class RepostTests(TestCase):

    def setUp(self):
        self.author = create_user()
        self.reposter = create_user(username="reposter", email="reposter@test.com")
        self.ribbit = create_ribbit(self.author, "Repost me!")
        self.client = get_auth_client(self.reposter)
        self.url = reverse("repost-with-opinion", kwargs={"pk": self.ribbit.pk})

    def test_repost_ribbit(self):
        response = self.client.post(self.url, {"text": "My take on this"}, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_repost_increments_count(self):
        self.client.post(self.url, {"text": ""}, format="json")
        self.ribbit.refresh_from_db()
        self.assertGreaterEqual(self.ribbit.reribbit_count, 1)


# ---------------------------------------------------------------------------
# Notification Tests
# ---------------------------------------------------------------------------
class NotificationTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.sender = create_user(username="sender", email="sender@test.com")
        self.client = get_auth_client(self.user)
        self.url = reverse("notifications")

    def test_get_notifications_authenticated(self):
        Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            notif_type="like",
            message="liked your ribbit",
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notifications_only_for_current_user(self):
        other = create_user(username="other3", email="other3@test.com")
        Notification.objects.create(
            sender=self.sender, receiver=other, notif_type="follow", message="followed you"
        )
        response = self.client.get(self.url)
        results = response.data.get("results") if "results" in response.data else response.data
        if len(results) > 0:
            print("ERROR: Test returned unexpected notifications:", results)
        self.assertEqual(len(results), 0)

    def test_unauthenticated_cannot_get_notifications(self):
        client = APIClient()
        response = client.get(self.url)
        if response.status_code == 200:
            print("ERROR: Unauthenticated user got 200 on notifications:")
            print(response.data)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
