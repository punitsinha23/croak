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
from unittest.mock import patch
from .models import Ribbit, Like, Comment, Notification, Reply, EmailQueue, EmailPreferences

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

    def test_post_author_can_delete_comment_on_their_post(self):
        comment = Comment.objects.create(ribbit=self.ribbit, author=self.commenter, text="Rude")
        url = reverse("delete_comment", kwargs={"ribbit_id": self.ribbit.pk, "comment_id": comment.pk})
        response = get_auth_client(self.author).delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_stranger_cannot_delete_comment(self):
        stranger = create_user(username="stranger", email="stranger@test.com")
        comment = Comment.objects.create(ribbit=self.ribbit, author=self.commenter, text="Keep me")
        url = reverse("delete_comment", kwargs={"ribbit_id": self.ribbit.pk, "comment_id": comment.pk})
        response = get_auth_client(stranger).delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)


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


class InteractionNotificationTests(TestCase):

    def setUp(self):
        self.author = create_user()
        self.fan = create_user(username="fan", email="fan@test.com")
        self.ribbit = create_ribbit(self.author)
        self.client = get_auth_client(self.fan)
        self.like_url = reverse("like-ribbit", kwargs={"pk": self.ribbit.pk})

    def test_like_notifies_author(self):
        self.client.post(self.like_url)
        notif = Notification.objects.get(receiver=self.author)
        self.assertEqual(notif.notif_type, "like")
        self.assertEqual(notif.sender, self.fan)
        self.assertEqual(notif.post, self.ribbit)

    def test_unlike_removes_like_notification(self):
        self.client.post(self.like_url)
        self.client.post(self.like_url)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(Like.objects.count(), 0)

    def test_liking_own_ribbit_does_not_notify(self):
        get_auth_client(self.author).post(self.like_url)
        self.assertEqual(Like.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 0)

    def test_like_response_reports_count(self):
        response = self.client.post(self.like_url)
        self.assertEqual(response.data["status"], "liked")
        self.assertEqual(response.data["likes_count"], 1)
        self.assertTrue(response.data["is_liked"])

    def test_comment_notifies_author(self):
        self.client.post(reverse("comments", kwargs={"pk": self.ribbit.pk}), {"text": "Love it"})
        notif = Notification.objects.get(receiver=self.author)
        self.assertEqual(notif.notif_type, "comment")

    def test_commenting_on_own_ribbit_does_not_notify(self):
        get_auth_client(self.author).post(reverse("comments", kwargs={"pk": self.ribbit.pk}), {"text": "Self"})
        self.assertEqual(Notification.objects.count(), 0)


class ReplyTests(TestCase):

    def setUp(self):
        self.author = create_user()
        self.commenter = create_user(username="commenter2", email="commenter2@test.com")
        self.replier = create_user(username="replier", email="replier@test.com")
        self.ribbit = create_ribbit(self.author)
        self.comment = Comment.objects.create(ribbit=self.ribbit, author=self.commenter, text="First!")
        self.url = reverse("comment-replies", kwargs={"comment_id": self.comment.pk})

    def test_reply_to_comment(self):
        response = get_auth_client(self.replier).post(self.url, {"text": "Agreed"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reply.objects.get().comment, self.comment)

    def test_reply_notifies_comment_author(self):
        get_auth_client(self.replier).post(self.url, {"text": "Agreed"})
        notif = Notification.objects.get(receiver=self.commenter)
        self.assertEqual(notif.notif_type, "reply")
        self.assertEqual(notif.post, self.ribbit)

    def test_list_replies_only_for_that_comment(self):
        other = Comment.objects.create(ribbit=self.ribbit, author=self.author, text="Other")
        Reply.objects.create(comment=self.comment, author=self.replier, text="Here")
        Reply.objects.create(comment=other, author=self.replier, text="Not here")
        response = get_auth_client(self.replier).get(self.url)
        results = response.data.get("results", response.data)
        self.assertEqual([r["text"] for r in results], ["Here"])


class RepostDetailTests(TestCase):

    def setUp(self):
        self.author = create_user()
        self.reposter = create_user(username="reposter2", email="reposter2@test.com")
        self.ribbit = create_ribbit(self.author, "Original")

    def test_repost_links_to_original_and_keeps_opinion(self):
        url = reverse("repost-with-opinion", kwargs={"pk": self.ribbit.pk})
        get_auth_client(self.reposter).post(url, {"repost_text": "So true"}, format="json")
        repost = Ribbit.objects.get(author=self.reposter)
        self.assertTrue(repost.is_reribbit)
        self.assertEqual(repost.reribbit_of, self.ribbit)
        self.assertEqual(repost.text, "So true")

    def test_owner_can_edit_ribbit(self):
        url = reverse("edit", kwargs={"pk": self.ribbit.pk})
        response = get_auth_client(self.author).patch(url, {"text": "Edited"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ribbit.refresh_from_db()
        self.assertEqual(self.ribbit.text, "Edited")

    def test_non_owner_cannot_edit_ribbit(self):
        url = reverse("edit", kwargs={"pk": self.ribbit.pk})
        response = get_auth_client(self.reposter).patch(url, {"text": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.ribbit.refresh_from_db()
        self.assertEqual(self.ribbit.text, "Original")


class FeedPaginationTests(TestCase):

    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        self.user = create_user()
        self.other = create_user(username="other4", email="other4@test.com")
        now = timezone.now()
        for i in range(12):
            Ribbit.objects.create(author=self.user, text=f"post {i}", created_at=now - timedelta(minutes=i))
        Ribbit.objects.create(author=self.other, text="other post", created_at=now - timedelta(hours=1))
        self.client = get_auth_client(self.user)

    def test_feed_is_newest_first_in_pages_of_ten(self):
        response = self.client.get(reverse("feed"))
        texts = [r["text"] for r in response.data["results"]]
        self.assertEqual(len(texts), 10)
        self.assertEqual(texts[0], "post 0")
        self.assertIsNotNone(response.data["next"])

    def test_next_page_continues_where_first_stopped(self):
        first = self.client.get(reverse("feed"))
        second = self.client.get(first.data["next"])
        texts = [r["text"] for r in second.data["results"]]
        self.assertEqual(texts, ["post 10", "post 11", "other post"])
        self.assertIsNone(second.data["next"])

    def test_filter_feed_by_username(self):
        response = self.client.get(reverse("feed"), {"username": "other4"})
        self.assertEqual([r["text"] for r in response.data["results"]], ["other post"])


class NewPostEmailSignalTests(TestCase):

    def setUp(self):
        self.author = create_user()
        self.follower = create_user(username="follower", email="follower@test.com")
        self.follower.following.add(self.author)

    def test_original_post_queues_email_for_followers(self):
        create_ribbit(self.author, "Big news")
        email = EmailQueue.objects.get()
        self.assertEqual(email.recipient, self.follower)
        self.assertEqual(email.status, "pending")

    def test_reply_and_repost_do_not_queue_emails(self):
        original = Ribbit.objects.create(author=self.follower, text="Mine")
        Ribbit.objects.create(author=self.author, text="reply", parent=original)
        Ribbit.objects.create(author=self.author, text="", is_reribbit=True, reribbit_of=original)
        self.assertEqual(EmailQueue.objects.filter(recipient=self.follower).count(), 0)

    def test_follower_who_opted_out_gets_no_email(self):
        EmailPreferences.objects.create(user=self.follower, email_on_new_post_from_following=False)
        create_ribbit(self.author)
        self.assertEqual(EmailQueue.objects.count(), 0)

    def test_master_switch_off_gets_no_email(self):
        EmailPreferences.objects.create(user=self.follower, email_enabled=False)
        create_ribbit(self.author)
        self.assertEqual(EmailQueue.objects.count(), 0)


@patch.dict("os.environ", {"CRON_SECRET": "test-cron-secret"})
class CronEndpointTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.email = EmailQueue.objects.create(
            recipient=self.user, email_type="instant", subject="Hi", body_html="<p>Hi</p>", body_text="Hi",
        )
        self.url = reverse("cron-process-emails")
        self.headers = {"HTTP_X_CRON_SECRET": "test-cron-secret"}

    def test_wrong_secret_is_rejected(self):
        response = self.client.post(self.url, HTTP_X_CRON_SECRET="nope")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_secret_is_rejected(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("ribbits.email_queue.requests.post")
    def test_successful_send_marks_email_sent(self, mock_post):
        mock_post.return_value.status_code = 200
        response = self.client.post(self.url, **self.headers)
        self.assertEqual(response.data["sent"], 1)
        self.email.refresh_from_db()
        self.assertEqual(self.email.status, "sent")
        self.assertIsNotNone(self.email.sent_at)
        self.assertEqual(mock_post.call_args.kwargs["json"]["to"], self.user.email)

    @patch("ribbits.email_queue.requests.post")
    def test_failed_send_is_retried_then_marked_failed(self, mock_post):
        mock_post.return_value.status_code = 500
        for expected_status in ["pending", "pending", "failed"]:
            self.client.post(self.url, **self.headers)
            self.email.refresh_from_db()
            self.assertEqual(self.email.status, expected_status)
        self.assertEqual(self.email.retry_count, 3)
        self.client.post(self.url, **self.headers)
        self.assertEqual(mock_post.call_count, 3)

    @patch("ribbits.email_queue.requests.post", side_effect=ConnectionError("service down"))
    def test_service_down_counts_as_failure(self, mock_post):
        response = self.client.post(self.url, **self.headers)
        self.assertEqual(response.data["failed"], 1)
        self.email.refresh_from_db()
        self.assertEqual(self.email.retry_count, 1)
        self.assertIn("service down", self.email.error_message)

    def test_future_scheduled_email_is_not_sent_yet(self):
        from datetime import timedelta
        from django.utils import timezone
        EmailQueue.objects.update(scheduled_for=timezone.now() + timedelta(hours=1))
        with patch("ribbits.email_queue.requests.post") as mock_post:
            response = self.client.post(self.url, **self.headers)
        self.assertEqual(response.data["sent"], 0)
        mock_post.assert_not_called()

    @patch("ribbits.email_queue.requests.post")
    def test_each_email_is_sent_only_once_across_runs(self, mock_post):
        from .email_queue import send_due_emails
        mock_post.return_value.status_code = 200
        self.assertEqual(send_due_emails(), (1, 1, 0))
        self.assertEqual(send_due_emails(), (0, 0, 0))
        self.assertEqual(mock_post.call_count, 1)

    def test_run_stops_when_time_budget_is_used_up(self):
        from .email_queue import send_due_emails
        with patch("ribbits.email_queue.requests.post") as mock_post:
            self.assertEqual(send_due_emails(time_budget_seconds=0), (0, 0, 0))
        mock_post.assert_not_called()
        self.email.refresh_from_db()
        self.assertEqual(self.email.status, "pending")

    @patch("ribbits.email_queue.requests.post")
    def test_email_stuck_in_processing_is_retried_later(self, mock_post):
        from datetime import timedelta
        from django.utils import timezone
        from .email_queue import send_due_emails
        mock_post.return_value.status_code = 200
        EmailQueue.objects.update(status="processing", claimed_at=timezone.now() - timedelta(minutes=11))
        self.assertEqual(send_due_emails(), (1, 1, 0))
        self.email.refresh_from_db()
        self.assertEqual(self.email.status, "sent")

    @patch("ribbits.email_queue.requests.post")
    def test_email_claimed_moments_ago_is_left_to_its_run(self, mock_post):
        from django.utils import timezone
        from .email_queue import send_due_emails
        EmailQueue.objects.update(status="processing", claimed_at=timezone.now())
        self.assertEqual(send_due_emails(), (0, 0, 0))
        mock_post.assert_not_called()

    @patch("ribbits.email_queue.requests.post")
    def test_each_sent_email_is_recorded_immediately(self, mock_post):
        from .email_queue import send_due_emails
        second = EmailQueue.objects.create(
            recipient=self.user, email_type="instant", subject="Two", body_html="<p>2</p>", body_text="2",
        )
        statuses_seen_during_second_send = []

        def fake_post(*args, **kwargs):
            if kwargs["json"]["subject"] == "Two":
                statuses_seen_during_second_send.append(EmailQueue.objects.get(pk=self.email.pk).status)
            return type("Response", (), {"status_code": 200})()

        mock_post.side_effect = fake_post
        send_due_emails()
        self.assertEqual(statuses_seen_during_second_send, ["sent"])
        second.refresh_from_db()
        self.assertEqual(second.status, "sent")

    def test_stats_endpoint_reports_pending(self):
        response = self.client.get(reverse("cron-stats"), {"secret": "test-cron-secret"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pending"], 1)


class EmailPreferencesApiTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = get_auth_client(self.user)
        self.url = reverse("email-preferences")

    def test_get_creates_defaults(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["email_enabled"])
        self.assertTrue(EmailPreferences.objects.filter(user=self.user).exists())

    def test_patch_updates_only_own_preferences(self):
        other = create_user(username="other5", email="other5@test.com")
        EmailPreferences.objects.create(user=other)
        response = self.client.patch(self.url, {"daily_digest": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(EmailPreferences.objects.get(user=self.user).daily_digest)
        self.assertTrue(EmailPreferences.objects.get(user=other).daily_digest)

    def test_unauthenticated_cannot_read_preferences(self):
        response = APIClient().get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NewPostBroadcastTests(TestCase):

    def setUp(self):
        self.author = create_user(username="author", email="author@test.com")
        self.follower = create_user(username="follower2", email="follower2@test.com")
        self.stranger = create_user(username="stranger2", email="stranger2@test.com")
        self.follower.following.add(self.author)

    def emails_for(self, user):
        return EmailQueue.objects.filter(recipient=user, email_type="new_post")

    def test_everyone_except_author_is_emailed(self):
        create_ribbit(self.author, "Hello everyone")
        self.assertEqual(self.emails_for(self.follower).count(), 1)
        self.assertEqual(self.emails_for(self.stranger).count(), 1)
        self.assertEqual(self.emails_for(self.author).count(), 0)

    def test_followers_and_others_get_different_subjects(self):
        create_ribbit(self.author, "Big news today")
        self.assertIn("just croaked", self.emails_for(self.follower).get().subject)
        self.assertIn("Fresh on Croak", self.emails_for(self.stranger).get().subject)

    def test_anyone_opt_out_only_affects_non_followers(self):
        EmailPreferences.objects.create(user=self.stranger, email_on_new_post_from_anyone=False)
        EmailPreferences.objects.create(user=self.follower, email_on_new_post_from_anyone=False)
        create_ribbit(self.author)
        self.assertEqual(self.emails_for(self.stranger).count(), 0)
        self.assertEqual(self.emails_for(self.follower).count(), 1)

    def test_inactive_and_emailless_users_are_skipped(self):
        inactive = create_user(username="gone", email="gone@test.com")
        inactive.is_active = False
        inactive.save()
        no_email = create_user(username="noemail", email="placeholder@test.com")
        User.objects.filter(pk=no_email.pk).update(email="")
        create_ribbit(self.author)
        self.assertEqual(self.emails_for(inactive).count(), 0)
        self.assertEqual(self.emails_for(no_email).count(), 0)

    def test_burst_of_posts_sends_one_pending_email_per_person(self):
        create_ribbit(self.author, "one")
        create_ribbit(self.author, "two")
        create_ribbit(self.author, "three")
        self.assertEqual(self.emails_for(self.stranger).count(), 1)

    def test_new_email_queued_once_previous_one_was_sent(self):
        create_ribbit(self.author, "one")
        EmailQueue.objects.update(status="sent")
        create_ribbit(self.author, "two")
        self.assertEqual(self.emails_for(self.stranger).filter(status="pending").count(), 1)

    def test_post_text_is_escaped_and_links_to_profile(self):
        create_ribbit(self.author, '<a href="https://evil.test">click</a>')
        html = self.emails_for(self.stranger).get().body_html
        self.assertNotIn('<a href="https://evil.test">', html)
        self.assertIn("&lt;a href=", html)
        self.assertIn("https://croak-green-shine.vercel.app/user/author", html)


class EveningCheckinTests(TestCase):

    def setUp(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        self.ist = ZoneInfo("Asia/Kolkata")
        self.at_730pm = datetime(2026, 10, 24, 19, 30, tzinfo=self.ist)
        self.poster = create_user(username="poster", email="poster@test.com")
        self.reader = create_user(username="reader", email="reader@test.com")

    def queue(self, now=None):
        from .email_queue import queue_evening_checkins
        return queue_evening_checkins(now=now or self.at_730pm)

    def post_at(self, text, hour, likes=0, day=24):
        from datetime import datetime
        ribbit = Ribbit.objects.create(author=self.poster, text=text, created_at=datetime(2026, 10, day, hour, 0, tzinfo=self.ist))
        for i in range(likes):
            fan = create_user(username=f"fan{text[:3]}{i}", email=f"fan{text[:3]}{i}@test.com")
            EmailPreferences.objects.create(user=fan, evening_checkin=False)
            Like.objects.create(ribbit=ribbit, user=fan)
        EmailQueue.objects.all().delete()
        return ribbit

    def test_queued_for_8pm_india_time(self):
        from datetime import datetime
        self.assertEqual(self.queue(), 2)
        email = EmailQueue.objects.filter(email_type="evening").first()
        self.assertEqual(email.scheduled_for, datetime(2026, 10, 24, 20, 0, tzinfo=self.ist))

    def test_running_after_8pm_sends_right_away(self):
        from datetime import datetime
        late = datetime(2026, 10, 24, 21, 15, tzinfo=self.ist)
        self.queue(now=late)
        self.assertEqual(EmailQueue.objects.filter(email_type="evening").first().scheduled_for, late)

    def test_running_twice_does_not_double_send(self):
        self.queue()
        self.assertEqual(self.queue(), 0)
        self.assertEqual(EmailQueue.objects.filter(email_type="evening").count(), 2)

    def test_opted_out_users_are_skipped(self):
        EmailPreferences.objects.create(user=self.reader, evening_checkin=False)
        EmailPreferences.objects.create(user=self.poster, email_enabled=False)
        self.assertEqual(self.queue(), 0)

    def test_includes_todays_top_posts_most_loved_first(self):
        self.post_at("quiet morning thought", 9, likes=1)
        self.post_at("everyone loved this", 12, likes=3)
        self.post_at("from yesterday", 12, likes=9, day=23)
        self.queue()
        html = EmailQueue.objects.get(recipient=self.reader, email_type="evening").body_html
        self.assertIn("2 croaks", html)
        self.assertNotIn("from yesterday", html)
        self.assertLess(html.index("everyone loved this"), html.index("quiet morning thought"))

    def test_quiet_day_invites_the_first_post(self):
        self.queue()
        email = EmailQueue.objects.get(recipient=self.reader, email_type="evening")
        self.assertIn("quiet in the pond", email.body_html)
        self.assertIn("https://croak-green-shine.vercel.app/index", email.body_html)

    def test_post_text_is_escaped(self):
        self.post_at("<img src=x onerror=alert(1)>", 10)
        self.queue()
        html = EmailQueue.objects.get(recipient=self.reader, email_type="evening").body_html
        self.assertNotIn("<img src=x", html)

    def test_prompt_changes_each_day(self):
        from datetime import timedelta
        self.queue()
        self.queue(now=self.at_730pm + timedelta(days=1))
        subjects = set(EmailQueue.objects.filter(recipient=self.reader).values_list("subject", flat=True))
        self.assertEqual(len(subjects), 2)

    @patch.dict("os.environ", {"CRON_SECRET": "test-cron-secret"})
    def test_cron_endpoint_requires_secret(self):
        client = APIClient()
        url = reverse("cron-evening-checkin")
        self.assertEqual(client.post(url, HTTP_X_CRON_SECRET="wrong").status_code, status.HTTP_403_FORBIDDEN)
        response = client.post(url, HTTP_X_CRON_SECRET="test-cron-secret")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["queued"], 2)

    def test_preferences_api_exposes_new_toggles(self):
        client = get_auth_client(self.reader)
        response = client.patch(reverse("email-preferences"), {"evening_checkin": False, "email_on_new_post_from_anyone": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prefs = EmailPreferences.objects.get(user=self.reader)
        self.assertFalse(prefs.evening_checkin)
        self.assertFalse(prefs.email_on_new_post_from_anyone)
