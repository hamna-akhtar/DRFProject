""" tests for friends urls """

from django.test import TestCase
from django.urls import resolve, reverse
from friends import views


class FriendURLsTests(TestCase):
    """tests to ensure that friends app urls correctly resolve to their views"""

    def test_friend_request_list_url_is_resolved(self):
        """friend requests list url resolves to FriendRequestListCreateView"""
        url = reverse("friends:friendrequest-list")
        self.assertEqual(url, "/friend-requests/")
        self.assertEqual(
            resolve(url).func.view_class, views.FriendRequestListCreateView
        )

    def test_friend_request_detail_url_is_resolved(self):
        """friend request detail url resolves to FriendRequestDetailView"""
        url = reverse("friends:friendrequest-detail", args=[1])
        self.assertEqual(url, "/friend-requests/1/")
        self.assertEqual(resolve(url).func.view_class, views.FriendRequestDetailView)

    def test_friend_request_sent_url_is_resolved(self):
        """friend requests sent url resolves to RequestsSentView"""
        url = reverse("friends:friendrequest-sent")
        self.assertEqual(url, "/friend-requests/sent/")
        self.assertEqual(resolve(url).func.view_class, views.RequestsSentView)

    def test_friend_request_received_url_is_resolved(self):
        """friend requests received url resolves to RequestsReceivedView"""
        url = reverse("friends:friendrequest-received")
        self.assertEqual(url, "/friend-requests/received/")
        self.assertEqual(resolve(url).func.view_class, views.RequestsReceivedView)
