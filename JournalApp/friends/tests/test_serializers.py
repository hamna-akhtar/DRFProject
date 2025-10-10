from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request
from users.models import CustomUser
from ..models import FriendRequest
from ..serializers import FriendRequestSerializer, FriendAcceptSerializer


class FriendRequestSerializerTests(TestCase):

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

    def create_request_context(self, user):
        request = self.factory.get("/")
        force_authenticate(request, user=user)
        request.user = user
        return {"request": Request(request)}

    def test_serialize_friend_request_includes_all_fields(self):
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
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        context = self.create_request_context(self.user1)
        serializer = FriendRequestSerializer(friend_request, context=context)
        data = serializer.data

        self.assertIsInstance(data["request_from"], dict)
        self.assertIsInstance(data["request_to"], dict)

    def test_serialize_created_at_and_accepted_are_read_only(self):
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        context = self.create_request_context(self.user1)
        serializer = FriendRequestSerializer(friend_request, context=context)

        self.assertTrue(serializer.fields["created_at"].read_only)
        self.assertTrue(serializer.fields["created_at"].read_only)

    def test_deserialize_valid_friend_request(self):
        context = self.create_request_context(self.user1)
        data = {"send_request_to": self.user2.id}

        serializer = FriendRequestSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["requested_to"], self.user2)

    def test_deserialize_send_request_to_is_required(self):
        context = self.create_request_context(self.user1)
        data = {}

        serializer = FriendRequestSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("send_request_to", serializer.errors)

    def test_deserialize_queryset_excludes_current_user_and_existing_sent_and_received_requests_users(
        self,
    ):
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
        context = self.create_request_context(self.user1)
        data = {"send_request_to": 99999}

        serializer = FriendRequestSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("send_request_to", serializer.errors)

    def test_deserialize_cannot_set_accepted(self):
        context = self.create_request_context(self.user1)
        data = {
            "send_request_to": self.user2.id,
            "accepted": True,
        }

        serializer = FriendRequestSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn("accepted", serializer.validated_data)


class FriendAcceptSerializerTests(TestCase):

    def setUp(self):
        self.user1 = CustomUser.objects.create(
            email="user1@gmail.com", password="abcdef"
        )
        self.user2 = CustomUser.objects.create(
            email="user2@gmail.com", password="ghijkl"
        )

    def test_serialize_only_accepted_field(self):
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        serializer = FriendAcceptSerializer(friend_request)
        data = serializer.data

        self.assertEqual(len(data), 1)
        self.assertIn("accepted", data)

    def test_deserialize_accept_request(self):
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        data = {"accepted": True}
        serializer = FriendAcceptSerializer(friend_request, data=data, partial=True)

        self.assertTrue(serializer.is_valid())
        self.assertTrue(serializer.validated_data["accepted"])

    def test_deserialize_unaccept_request(self):
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2, accepted=True
        )
        data = {"accepted": False}
        serializer = FriendAcceptSerializer(friend_request, data=data, partial=True)

        self.assertTrue(serializer.is_valid())
        self.assertFalse(serializer.validated_data["accepted"])
