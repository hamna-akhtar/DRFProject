from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from ..models import CustomUser
from .. import views
from journals.models import JournalEntry
from friends.models import FriendRequest
from svix.webhooks import WebhookVerificationError
from unittest.mock import patch, Mock
import json

class UserViewsTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user1 = CustomUser.objects.create(
            email="user1@gmail.com", password="abcdef"
        )
        self.user2 = CustomUser.objects.create(
            email="user2@gmail.com", password="ghijkl"
        )
        self.user3 = CustomUser.objects.create(
            email="user3@gmail.com", password="mnopqr"
        )

    # UserListView
    def test_user_list_requires_authentication(self):
        view = views.UserListView.as_view()
        request = self.factory.get("/users/")

        # without auth
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_list_returns_all_users(self):
        request = self.factory.get("/users/")
        force_authenticate(request, user=self.user1)
        view = views.UserListView.as_view()
        response = view(request)
        response.render()

        self.assertEqual(len(response.data), 3)
        emails = [user["email"] for user in response.data]
        self.assertIn("user1@gmail.com", emails)
        self.assertIn("user2@gmail.com", emails)
        self.assertIn("user3@gmail.com", emails)

    # MyProfileView
    def test_my_profile_requires_authentication(self):
        view = views.MyProfileView.as_view()
        request = self.factory.get("/users/my-profile/")

        # without auth
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_my_profile_returns_current_user(self):
        journal = JournalEntry.objects.create(
            author=self.user1, content="Private", access="private"
        )
        self.user1.friends.add(self.user2)

        request = self.factory.get("/users/my-profile/")
        force_authenticate(request, user=self.user1)
        view = views.MyProfileView.as_view()
        response = view(request)
        response.render()

        self.assertEqual(response.data["id"], self.user1.id)
        self.assertEqual(response.data["email"], "user1@gmail.com")
        self.assertEqual(journal.id, response.data["journal_entries"][0]["id"])
        self.assertEqual(self.user2.id, response.data["friends"][0]["id"])

    # UserDetailView
    def test_user_detail_requires_authentication(self):
        view = views.UserDetailView.as_view()
        request = self.factory.get(f"/users/{self.user1.id}/")

        # without auth
        response = view(request, pk=self.user1.pk)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user1)
        response = view(request, pk=self.user1.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_detail_returns_correct_user(self):
        request = self.factory.get(f"/users/{self.user2.pk}/")
        force_authenticate(request, user=self.user1)
        view = views.UserDetailView.as_view()
        response = view(request, pk=self.user2.pk)
        response.render()

        self.assertEqual(response.data["id"], self.user2.id)
        self.assertEqual(response.data["email"], "user2@gmail.com")

    def test_user_detail_can_update_own_profile_only(self):
        data = {"first_name": "new"}
        request = self.factory.patch(f"/users/{self.user1.id}/", data, format="json")
        view = views.UserDetailView.as_view()

        # can update own profile
        force_authenticate(request, user=self.user1)
        response = view(request, pk=self.user1.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.first_name, "new")

        # cannot update others profile
        force_authenticate(request, user=self.user2)
        response = view(request, pk=self.user1.pk)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # DiscoverFriendsView
    def test_discover_friends_requires_authentication(self):
        view = views.DiscoverFriendsView.as_view()
        request = self.factory.get("/users/discover/")

        # without auth
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_discover_friends_excludes_self_and_already_requested_users(self):
        user4 = CustomUser.objects.create(email="user4@gmail.com", password="stuvw")
        FriendRequest.objects.create(requested_by=self.user1, requested_to=self.user2)
        FriendRequest.objects.create(requested_by=self.user3, requested_to=self.user1)

        request = self.factory.get("/users/discover/")
        force_authenticate(request, user=self.user1)
        view = views.DiscoverFriendsView.as_view()
        response = view(request)
        response.render()

        user_ids = [user["id"] for user in response.data]
        self.assertNotIn(self.user1.id, user_ids)
        self.assertNotIn(self.user2.id, user_ids)
        self.assertNotIn(self.user3.id, user_ids)
        self.assertIn(user4.id, user_ids)


class ClerkWebhookTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("users.views.Webhook")
    def test_webhook_creates_new_user(self, mock_webhook_class):
        mock_webhook = Mock()
        mock_webhook_class.return_value = mock_webhook
        mock_webhook.verify.return_value = {
            "type": "user.created",
            "data": {
                "id": "123456",
                "email_addresses": [{"email_address": "new-user@gmail.com"}],
                "first_name": "new",
                "last_name": "user",
            },
        }

        request = self.factory.post(
            "/api/webhooks/",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_SVIX_ID="test-id",
            HTTP_SVIX_TIMESTAMP="test-timestamp",
            HTTP_SVIX_SIGNATURE="test-signature",
        )

        response = views.clerk_webhook(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CustomUser.objects.filter(clerk_id="123456").exists())
        user = CustomUser.objects.get(clerk_id="123456")
        self.assertEqual(user.email, "new-user@gmail.com")
        self.assertEqual(user.first_name, "new")
        self.assertEqual(user.last_name, "user")

    @patch("users.views.Webhook")
    def test_webhook_updates_existing_user(self, mock_webhook_class):
        CustomUser.objects.create(
            email="old@gmail.com",
            clerk_id="123456",
            first_name="old",
            password="abcdef",
        )

        mock_webhook = Mock()
        mock_webhook_class.return_value = mock_webhook
        mock_webhook.verify.return_value = {
            "type": "user.updated",
            "data": {
                "id": "123456",
                "email_addresses": [{"email_address": "new-user@gmail.com"}],
                "first_name": "new",
                "last_name": "user",
            },
        }

        request = self.factory.post(
            "/api/webhooks/",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_SVIX_ID="test-id",
            HTTP_SVIX_TIMESTAMP="test-timestamp",
            HTTP_SVIX_SIGNATURE="test-signature",
        )

        response = views.clerk_webhook(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = CustomUser.objects.get(clerk_id="123456")
        self.assertEqual(user.email, "new-user@gmail.com")
        self.assertEqual(user.first_name, "new")
        self.assertEqual(user.last_name, "user")

    @patch("users.views.Webhook")
    def test_webhook_deletes_user(self, mock_webhook_class):
        CustomUser.objects.create(
            email="user@gmail.com", clerk_id="123456", password="abcdef"
        )

        mock_webhook = Mock()
        mock_webhook_class.return_value = mock_webhook
        mock_webhook.verify.return_value = {
            "type": "user.deleted",
            "data": {"id": "123456"},
        }

        request = self.factory.post(
            "/api/webhooks/",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_SVIX_ID="test-id",
            HTTP_SVIX_TIMESTAMP="test-timestamp",
            HTTP_SVIX_SIGNATURE="test-signature",
        )

        response = views.clerk_webhook(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CustomUser.objects.filter(clerk_id="123456").exists())

    def test_webhook_rejects_non_post_requests(self):
        request = self.factory.get("/api/webhooks/")
        response = views.clerk_webhook(request)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid method")

    def test_webhook_rejects_missing_svix_headers(self):
        request = self.factory.post(
            "/api/webhooks/", data=json.dumps({}), content_type="application/json"
        )
        response = views.clerk_webhook(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Missing svix headers")

    @patch("users.views.Webhook")
    def test_webhook_handles_update_or_create_for_new_user(self, mock_webhook_class):
        self.assertFalse(CustomUser.objects.filter(clerk_id="123456").exists())

        mock_webhook = Mock()
        mock_webhook_class.return_value = mock_webhook
        mock_webhook.verify.return_value = {
            "type": "user.updated",
            "data": {
                "id": "123456",
                "email_addresses": [{"email_address": "new-user@gmail.com"}],
                "first_name": "new",
                "last_name": "user",
            },
        }
        request = self.factory.post(
            "/api/webhooks/",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_SVIX_ID="test-id",
            HTTP_SVIX_TIMESTAMP="test-timestamp",
            HTTP_SVIX_SIGNATURE="test-signature",
        )

        response = views.clerk_webhook(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CustomUser.objects.filter(clerk_id="123456").exists())

    @patch("users.views.Webhook")
    def test_webhook_handles_get_or_create_for_existing_user(self, mock_webhook_class):
        CustomUser.objects.create(
            email="user@gmail.com",
            clerk_id="123456",
            first_name="user",
            password="abcdef",
        )

        mock_webhook = Mock()
        mock_webhook_class.return_value = mock_webhook
        mock_webhook.verify.return_value = {
            "type": "user.created",
            "data": {
                "id": "123456",
                "email_addresses": [{"email_address": "user@gmail.com"}],
            },
        }
        request = self.factory.post(
            "/api/webhooks/",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_SVIX_ID="test-id",
            HTTP_SVIX_TIMESTAMP="test-timestamp",
            HTTP_SVIX_SIGNATURE="test-signature",
        )

        response = views.clerk_webhook(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CustomUser.objects.filter(clerk_id="123456").count(), 1)

    @patch("users.views.Webhook")
    def test_webhook_handles_invalid_signature(self, mock_webhook_class):
        mock_webhook = Mock()
        mock_webhook_class.return_value = mock_webhook
        mock_webhook.verify.side_effect = WebhookVerificationError("Invalid signature")

        request = self.factory.post(
            "/api/webhooks/",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_SVIX_ID="test-id",
            HTTP_SVIX_TIMESTAMP="test-timestamp",
            HTTP_SVIX_SIGNATURE="invalid-signature",
        )

        response = views.clerk_webhook(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid signature")

    @patch("users.views.Webhook")
    def test_webhook_handles_exception_for_missing_user_required_fields(
        self, mock_webhook_class
    ):
        mock_webhook = Mock()
        mock_webhook_class.return_value = mock_webhook
        mock_webhook.verify.return_value = {
            "type": "user.created",
            "data": {"id": "123456"},
        }

        request = self.factory.post(
            "/api/webhooks/",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_SVIX_ID="test-id",
            HTTP_SVIX_TIMESTAMP="test-timestamp",
            HTTP_SVIX_SIGNATURE="test-signature",
        )

        response = views.clerk_webhook(request)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch("users.views.Webhook")
    def test_webhook_returns_success_response(self, mock_webhook_class):
        mock_webhook = Mock()
        mock_webhook_class.return_value = mock_webhook
        mock_webhook.verify.return_value = {
            "type": "user.created",
            "data": {
                "id": "123456",
                "email_addresses": [{"email_address": "new-user@gmail.com"}],
                "first_name": "new",
                "last_name": "user",
            },
        }

        request = self.factory.post(
            "/api/webhooks/",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_SVIX_ID="test-id",
            HTTP_SVIX_TIMESTAMP="test-timestamp",
            HTTP_SVIX_SIGNATURE="test-signature",
        )
        response = views.clerk_webhook(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["event"], "user.created")
