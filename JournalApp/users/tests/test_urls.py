""" tests for users urls """

from django.test import TestCase
from django.urls import resolve, reverse
from users import views


class CustomUserURLsTests(TestCase):
    """tests to ensure that users app urls correctly resolve to their views"""

    def test_user_list_url_is_resolved(self):
        """user list url resolves to UserListView"""
        url = reverse("users:user-list")
        self.assertEqual(url, "/users/")
        self.assertEqual(resolve(url).func.view_class, views.UserListView)

    def test_user_detail_url_is_resolved(self):
        """user detail url resolves to UserDetailView"""
        url = reverse("users:user-detail", args=[1])
        self.assertEqual(url, "/users/1/")
        self.assertEqual(resolve(url).func.view_class, views.UserDetailView)

    def test_my_profile_url_is_resolved(self):
        """my profile url resolves to MyProfileView"""
        url = reverse("users:my-profile")
        self.assertEqual(url, "/users/my-profile/")
        self.assertEqual(resolve(url).func.view_class, views.MyProfileView)

    def test_discover_friends_url_is_resolved(self):
        """discover url resolves to DiscoverFriendsView"""
        url = reverse("users:user-discover")
        self.assertEqual(url, "/users/discover/")
        self.assertEqual(resolve(url).func.view_class, views.DiscoverFriendsView)

    def test_clerk_webhook_url_is_resolved(self):
        """webhooks url resolves to clerk_webhook view"""
        self.assertEqual(resolve("/api/webhooks/").func, views.clerk_webhook)
