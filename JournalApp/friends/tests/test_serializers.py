"""tests for friends serializers"""

from tests.base import CustomBaseTestCase
from friends.models import FriendRequest
from friends.serializers import FriendRequestSerializer, FriendAcceptSerializer


class FriendRequestSerializerTests(CustomBaseTestCase):
    """tests for FriendRequestSerializer"""

    def test_serialize_friend_request_includes_all_fields(self):
        """serialized FriendRequest includes all expected fields and excludes write-only ones"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        context = self.create_request_context(self.user1)
        serializer = FriendRequestSerializer(friend_request, context=context)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("created_at", data)
        self.assertIn("request_from", data)
        self.assertIn("request_to", data)
        self.assertIn("accepted", data)
        self.assertNotIn("send_request_to", data)

    def test_serialize_request_from_and_request_to_as_nested_objects(self):
        """request_from and request_to are represented as nested user objects"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        context = self.create_request_context(self.user1)
        serializer = FriendRequestSerializer(friend_request, context=context)
        data = serializer.data

        self.assertIsInstance(data["request_from"], dict)
        self.assertIsInstance(data["request_to"], dict)

    def test_serialize_created_at_and_accepted_are_read_only(self):
        """created_at and accepted fields are read only"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        context = self.create_request_context(self.user1)
        serializer = FriendRequestSerializer(friend_request, context=context)

        self.assertTrue(serializer.fields["created_at"].read_only)
        self.assertTrue(serializer.fields["created_at"].read_only)

    def test_deserialize_valid_friend_request(self):
        """deserialize valid friend request data and map to correct users"""
        context = self.create_request_context(self.user1)
        data = {"send_request_to": self.user2.id}

        serializer = FriendRequestSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["requested_to"], self.user2)

    def test_deserialize_send_request_to_is_required(self):
        """send_request_to field is required for deserializing"""
        context = self.create_request_context(self.user1)
        data = {}

        serializer = FriendRequestSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("send_request_to", serializer.errors)

    def test_deserialize_queryset_excludes_current_user_and_already_requested_users(
        self,
    ):
        """queryset for send_request_to excludes current user and already requested users"""
        FriendRequest.objects.create(requested_by=self.user1, requested_to=self.user2)
        FriendRequest.objects.create(requested_by=self.user3, requested_to=self.user1)

        context = self.create_request_context(self.user1)
        serializer = FriendRequestSerializer(context=context)
        fields = serializer.get_fields()
        queryset = fields["send_request_to"].queryset

        self.assertNotIn(self.user1, queryset)
        self.assertNotIn(self.user2, queryset)
        self.assertNotIn(self.user3, queryset)

    def test_deserialize_invalid_user_id(self):
        """reject invalid user_id as receiver when deserializing"""
        context = self.create_request_context(self.user1)
        data = {"send_request_to": 99999}

        serializer = FriendRequestSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("send_request_to", serializer.errors)

    def test_deserialize_cannot_set_accepted(self):
        """cannot manually set accepted field when creating friend request"""
        context = self.create_request_context(self.user1)
        data = {
            "send_request_to": self.user2.id,
            "accepted": True,
        }

        serializer = FriendRequestSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn("accepted", serializer.validated_data)


class FriendAcceptSerializerTests(CustomBaseTestCase):
    """tests for FriendAcceptSerializer"""

    def test_serialize_only_accepted_field(self):
        """only serialize the accepted field"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        serializer = FriendAcceptSerializer(friend_request)
        data = serializer.data

        self.assertEqual(len(data), 1)
        self.assertIn("accepted", data)

    def test_deserialize_accept_request(self):
        """correctly validate and accept friend request"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        data = {"accepted": True}
        serializer = FriendAcceptSerializer(friend_request, data=data, partial=True)

        self.assertTrue(serializer.is_valid())
        self.assertTrue(serializer.validated_data["accepted"])

    def test_deserialize_unaccept_request(self):
        """correctly validate and unaccept friend request"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2, accepted=True
        )
        data = {"accepted": False}
        serializer = FriendAcceptSerializer(friend_request, data=data, partial=True)

        self.assertTrue(serializer.is_valid())
        self.assertFalse(serializer.validated_data["accepted"])
