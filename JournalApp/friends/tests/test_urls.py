from django.test import TestCase
from django.urls import resolve, reverse
from .. import views


class FriendURLsTests(TestCase):

    def test_friend_request_list_url_is_resolved(self):
        url = reverse("friends:friendrequest-list")
        self.assertEqual(url, "/friend-requests/")
        self.assertEqual(
            resolve(url).func.view_class, views.FriendRequestListCreateView
        )

    def test_friend_request_detail_url_is_resolved(self):
        url = reverse("friends:friendrequest-detail", args=[1])
        self.assertEqual(url, "/friend-requests/1/")
        self.assertEqual(resolve(url).func.view_class, views.FriendRequestDetailView)

    def test_friend_request_sent_url_is_resolved(self):
        url = reverse("friends:friendrequest-sent")
        self.assertEqual(url, "/friend-requests/sent/")
        self.assertEqual(resolve(url).func.view_class, views.RequestsSentView)

    def test_friend_request_received_url_is_resolved(self):
        url = reverse("friends:friendrequest-received")
        self.assertEqual(url, "/friend-requests/received/")
        self.assertEqual(resolve(url).func.view_class, views.RequestsReceivedView)

