"""tests for friends models"""

from datetime import date
from tests.base import CustomBaseTestCase
from friends.models import FriendRequest


class FriendRequestModelTests(CustomBaseTestCase):
    """tests for FriendRequest model"""

    def test_friend_request_create_with_required_fields(self):
        """requested_by and requested_to are required fields for creating friend request"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        self.assertIsNotNone(friend_request.id)
        self.assertEqual(friend_request.requested_by, self.user1)
        self.assertEqual(friend_request.requested_to, self.user2)
        self.assertFalse(friend_request.accepted)
        self.assertEqual(friend_request.created_at, date.today())

    def test_friend_request_default_accepted_false(self):
        """accepted field is set to false by default if not defined when creating"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        self.assertFalse(friend_request.accepted)

    def test_friend_request_can_be_accepted(self):
        """friend request can be accepted when creating"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        friend_request.accepted = True
        friend_request.save()

        self.assertTrue(friend_request.accepted)

    def test_friend_request_created_at_auto_set(self):
        """created_at field is automatically set to present date on creation"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        self.assertIsNotNone(friend_request.created_at)
        self.assertEqual(friend_request.created_at, date.today())

    def test_friend_request_cascade_delete_on_requester_delete(self):
        """user deletion cascades to deletion of their sent requests"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        request_id = friend_request.id

        self.user1.delete()
        self.assertFalse(FriendRequest.objects.filter(id=request_id).exists())

    def test_friend_request_cascade_delete_on_receiver_delete(self):
        """user deletion cascades to deletion of their received requests"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        request_id = friend_request.id

        self.user2.delete()
        self.assertFalse(FriendRequest.objects.filter(id=request_id).exists())

    def test_friend_requests_sent_by_a_user(self):
        """a user can send multiple friends requests"""
        FriendRequest.objects.create(requested_by=self.user1, requested_to=self.user2)
        FriendRequest.objects.create(requested_by=self.user1, requested_to=self.user3)

        self.assertEqual(self.user1.requests_sent.count(), 2)

    def test_friend_requests_received_by_a_user(self):
        """a user can receive multiple friend requests"""
        FriendRequest.objects.create(requested_by=self.user1, requested_to=self.user2)
        FriendRequest.objects.create(requested_by=self.user3, requested_to=self.user2)

        self.assertEqual(self.user2.requests_received.count(), 2)
