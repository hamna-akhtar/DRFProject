from django.test import TestCase
from users.models import CustomUser
from ..models import FriendRequest
from datetime import date


class FriendRequestModelTests(TestCase):

    def setUp(self):
        self.user1 = CustomUser.objects.create(
            email="user1@gmail.com", password="abcdef"
        )
        self.user2 = CustomUser.objects.create(
            email="user2@gmail.com", password="ghijkl"
        )
        self.user3 = CustomUser.objects.create(
            email="user3@gmail.com", password="mnopqr"
        )

    def test_friend_request_create_with_required_fields(self):
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        self.assertIsNotNone(friend_request.id)
        self.assertEqual(friend_request.requested_by, self.user1)
        self.assertEqual(friend_request.requested_to, self.user2)
        self.assertFalse(friend_request.accepted)
        self.assertEqual(friend_request.created_at, date.today())

    def test_friend_request_default_accepted_false(self):
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        self.assertFalse(friend_request.accepted)

    def test_friend_request_can_be_accepted(self):
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        friend_request.accepted = True
        friend_request.save()

        self.assertTrue(friend_request.accepted)

    def test_friend_request_created_at_auto_set(self):
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        self.assertIsNotNone(friend_request.created_at)
        self.assertEqual(friend_request.created_at, date.today())

    def test_friend_request_cascade_delete_on_requester_delete(self):
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        request_id = friend_request.id

        self.user1.delete()
        self.assertFalse(FriendRequest.objects.filter(id=request_id).exists())

    def test_friend_request_cascade_delete_on_receiver_delete(self):
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        request_id = friend_request.id

        self.user2.delete()
        self.assertFalse(FriendRequest.objects.filter(id=request_id).exists())

    def test_friend_requests_sent_by_a_user(self):
        FriendRequest.objects.create(requested_by=self.user1, requested_to=self.user2)
        FriendRequest.objects.create(requested_by=self.user1, requested_to=self.user3)

        self.assertEqual(self.user1.requests_sent.count(), 2)

    def test_friend_requests_received_by_a_user(self):
        FriendRequest.objects.create(requested_by=self.user1, requested_to=self.user2)
        FriendRequest.objects.create(requested_by=self.user3, requested_to=self.user2)

        self.assertEqual(self.user2.requests_received.count(), 2)

