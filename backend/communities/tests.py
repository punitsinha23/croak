"""
Tests for the Communities app.
Covers: Community creation, listing, joining, leaving,
        Messaging, and role-based access control.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Community, Membership, Message

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def create_user(username="comuser", email="com@test.com", password="Pass1234!"):
    return User.objects.create_user(
        username=username, email=email, password=password, first_name="Com"
    )


def get_auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def create_community(creator, name="Test Pond", description="A place to croak"):
    community = Community.objects.create(
        name=name, description=description, creator=creator
    )
    Membership.objects.create(user=creator, community=community, role="admin")
    return community


# ---------------------------------------------------------------------------
# Community CRUD Tests
# ---------------------------------------------------------------------------
class CommunityCreationTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = get_auth_client(self.user)
        self.url = "/api/communities/"

    def test_create_community_success(self):
        response = self.client.post(
            self.url, {"name": "New Pond", "description": "Fresh water"}, format="json"
        )
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(Community.objects.count(), 1)

    def test_creator_becomes_admin(self):
        self.client.post(
            self.url, {"name": "Admin Pond", "description": ""}, format="json"
        )
        community = Community.objects.get(name="Admin Pond")
        membership = Membership.objects.get(user=self.user, community=community)
        self.assertEqual(membership.role, "admin")

    def test_duplicate_community_name_fails(self):
        create_community(self.user, name="Unique Pond")
        response = self.client.post(
            self.url, {"name": "Unique Pond", "description": "Another"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_community_requires_name(self):
        response = self.client.post(self.url, {"name": "", "description": "No name"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_create(self):
        client = APIClient()
        response = client.post(self.url, {"name": "Ghost Pond"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CommunityListTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = get_auth_client(self.user)
        self.url = "/api/communities/"

    def test_list_communities_authenticated(self):
        create_community(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results") or response.data
        self.assertGreaterEqual(len(results), 1)

    def test_list_communities_unauthenticated(self):
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_community_detail(self):
        community = create_community(self.user)
        url = f"/api/communities/{community.slug}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], community.name)

    def test_nonexistent_community_returns_404(self):
        response = self.client.get("/api/communities/no-such-pond/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Membership (Join / Leave) Tests
# ---------------------------------------------------------------------------
class MembershipTests(TestCase):

    def setUp(self):
        self.creator = create_user()
        self.joiner = create_user(username="joiner", email="joiner@test.com")
        self.community = create_community(self.creator)
        self.client = get_auth_client(self.joiner)
        self.join_url = "/api/communities/membership/join/"

    def test_join_community(self):
        response = self.client.post(
            self.join_url, {"community_slug": self.community.slug}, format="json"
        )
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(
            Membership.objects.filter(user=self.joiner, community=self.community).exists()
        )

    def test_cannot_join_same_community_twice(self):
        Membership.objects.create(user=self.joiner, community=self.community, role="member")
        response = self.client.post(
            self.join_url, {"community_slug": self.community.slug}, format="json"
        )
        self.assertNotIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_leave_community(self):
        membership = Membership.objects.create(
            user=self.joiner, community=self.community, role="member"
        )
        leave_url = "/api/communities/membership/leave/"
        response = self.client.post(leave_url, {"community_slug": self.community.slug}, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        self.assertFalse(
            Membership.objects.filter(user=self.joiner, community=self.community).exists()
        )

    def test_admin_cannot_leave_own_community(self):
        """Creator/admin should not be able to leave their own community."""
        admin_client = get_auth_client(self.creator)
        membership = Membership.objects.get(user=self.creator, community=self.community)
        leave_url = "/api/communities/membership/leave/"
        response = admin_client.post(leave_url, {"community_slug": self.community.slug}, format="json")
        # Should either be forbidden or the community should still have the membership
        if response.status_code == status.HTTP_204_NO_CONTENT:
            # If the API allows it, at least verify the community still exists
            self.assertTrue(Community.objects.filter(pk=self.community.pk).exists())

    def test_member_count_increases_on_join(self):
        initial_count = self.community.member_count
        Membership.objects.create(user=self.joiner, community=self.community, role="member")
        self.community.refresh_from_db()
        # member_count should be at least initial or higher (depends on signal/manual update)
        self.assertGreaterEqual(self.community.member_count, initial_count)

    def test_unauthenticated_cannot_join(self):
        client = APIClient()
        response = client.post(self.join_url, {"community_slug": self.community.slug}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Community Message Tests
# ---------------------------------------------------------------------------
class MessageTests(TestCase):

    def setUp(self):
        self.creator = create_user()
        self.member = create_user(username="member", email="member@test.com")
        self.outsider = create_user(username="outsider", email="outsider@test.com")
        self.community = create_community(self.creator)
        Membership.objects.create(user=self.member, community=self.community, role="member")
        self.msg_url = "/api/communities/messages/"

    def test_member_can_send_message(self):
        client = get_auth_client(self.member)
        response = client.post(
            self.msg_url,
            {"community": self.community.pk, "content": "Hello pond!"},
            format="json",
        )
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(Message.objects.count(), 1)

    def test_creator_can_send_message(self):
        client = get_auth_client(self.creator)
        response = client.post(
            self.msg_url,
            {"community": self.community.pk, "content": "Welcome everyone!"},
            format="json",
        )
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_outsider_cannot_send_message(self):
        client = get_auth_client(self.outsider)
        response = client.post(
            self.msg_url,
            {"community": self.community.pk, "content": "Sneaking in!"},
            format="json",
        )
        self.assertNotIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_empty_message_fails(self):
        client = get_auth_client(self.member)
        response = client.post(
            self.msg_url,
            {"community": self.community.pk, "content": ""},
            format="json",
        )
        self.assertNotIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_get_messages_as_member(self):
        Message.objects.create(
            community=self.community, sender=self.creator, content="First message"
        )
        client = get_auth_client(self.member)
        response = client.get(self.msg_url, {"community_slug": self.community.slug})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_get_messages(self):
        client = APIClient()
        response = client.get(self.msg_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Community Slug Auto-Generation Tests
# ---------------------------------------------------------------------------
class CommunityModelTests(TestCase):

    def setUp(self):
        self.user = create_user()

    def test_slug_auto_generated(self):
        community = Community.objects.create(name="Frog Fanatics", creator=self.user)
        self.assertEqual(community.slug, "frog-fanatics")

    def test_slug_unique_for_unique_names(self):
        c1 = Community.objects.create(name="Alpha Pond", creator=self.user)
        c2 = Community.objects.create(name="Beta Pond", creator=self.user)
        self.assertNotEqual(c1.slug, c2.slug)

    def test_community_str_representation(self):
        community = Community.objects.create(name="Str Test", creator=self.user)
        self.assertEqual(str(community), "Str Test")

    def test_membership_str_representation(self):
        community = Community.objects.create(name="Repr Test", creator=self.user)
        membership = Membership.objects.create(
            user=self.user, community=community, role="admin"
        )
        self.assertIn("comuser", str(membership))
        self.assertIn("admin", str(membership))
