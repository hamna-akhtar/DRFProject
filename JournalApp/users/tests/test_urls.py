from django.test import TestCase
from django.urls import resolve, reverse
from .. import views


class CustomUserURLsTests(TestCase):

    def test_user_list_url_is_resolved(self):
        url = reverse("users:user-list")
        self.assertEqual(url, "/users/")
        self.assertEqual(resolve(url).func.view_class, views.UserListView)

    def test_user_detail_url_is_resolved(self):
        url = reverse("users:user-detail", args=[1])
        self.assertEqual(url, "/users/1/")
        self.assertEqual(resolve(url).func.view_class, views.UserDetailView)

    def test_my_profile_url_is_resolved(self):
        url = reverse("users:my-profile")
        self.assertEqual(url, "/users/my-profile/")
        self.assertEqual(resolve(url).func.view_class, views.MyProfileView)

    def test_discover_friends_url_is_resolved(self):
        url = reverse("users:user-discover")
        self.assertEqual(url, "/users/discover/")
        self.assertEqual(resolve(url).func.view_class, views.DiscoverFriendsView)

    def test_clerk_webhook_url_is_resolved(self):
        self.assertEqual(resolve("/api/webhooks/").func, views.clerk_webhook)

