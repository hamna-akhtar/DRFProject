from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request
from ..models import CustomUser
from ..serializers import UserSerializer, UserMiniSerializer
from journals.models import JournalEntry, Task


class UserMiniSerializerTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create(
            email="user@gmail.com",
            first_name="ben",
            last_name="adams",
            password="abcdef",
        )

    def test_serialize_user_mini_includes_only_basic_fields(self):
        serializer = UserMiniSerializer(self.user)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("email", data)
        self.assertIn("first_name", data)
        self.assertIn("last_name", data)
        self.assertNotIn("password", data)
        self.assertNotIn("friends", data)
        self.assertNotIn("journal_entries", data)
        self.assertNotIn("tasks", data)
        self.assertNotIn("clerk_id", data)
        self.assertEqual(len(data), 4)

    def test_serialize_multiple_users_mini(self):
        CustomUser.objects.create(email="user2@gmail.com", password="ghijkl")
        CustomUser.objects.create(email="user3@gmail.com", password="mnopqr")

        users = CustomUser.objects.all()
        serializer = UserMiniSerializer(users, many=True)

        self.assertEqual(len(serializer.data), 3)
        emails = [user["email"] for user in serializer.data]
        self.assertIn("user@gmail.com", emails)
        self.assertIn("user2@gmail.com", emails)
        self.assertIn("user3@gmail.com", emails)


class UserSerializerTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user1 = CustomUser.objects.create(
            email="user1@gmail.com",
            first_name="ben",
            last_name="adams",
            password="abcdef",
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

    def test_serialize_user_includes_all_fields(self):
        context = self.create_request_context(self.user1)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("clerk_id", data)
        self.assertIn("first_name", data)
        self.assertIn("last_name", data)
        self.assertIn("email", data)
        self.assertIn("friends", data)
        self.assertIn("journal_entries", data)
        self.assertIn("tasks", data)
        self.assertEqual(len(data), 8)

    def test_serialize_own_profile_shows_all_journals_else_shows_public_or_shared(self):
        private = JournalEntry.objects.create(
            author=self.user1, content="abc", access="private"
        )
        public = JournalEntry.objects.create(
            author=self.user1, content="def", access="public"
        )
        shared = JournalEntry.objects.create(
            author=self.user1, content="ghi", access="custom"
        )
        shared.shared_to.add(self.user2)

        # own profile shows all
        context = self.create_request_context(self.user1)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data
        self.assertEqual(len(data["journal_entries"]), 3)
        self.assertEqual(data["journal_entries"][0]["id"], private.id)
        self.assertEqual(data["journal_entries"][1]["id"], public.id)
        self.assertEqual(data["journal_entries"][2]["id"], shared.id)

        # shared user's profile shows public and shared
        context = self.create_request_context(self.user2)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data
        self.assertEqual(len(data["journal_entries"]), 2)
        self.assertEqual(data["journal_entries"][0]["id"], public.id)
        self.assertEqual(data["journal_entries"][1]["id"], shared.id)

        # other's profile shows public only
        context = self.create_request_context(self.user3)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data
        self.assertEqual(len(data["journal_entries"]), 1)
        self.assertEqual(data["journal_entries"][0]["id"], public.id)

    def test_serialize_friends_list_visible_for_own_profile_or_friends_profile(self):
        self.user1.friends.add(self.user2)

        # own friend list visible
        context = self.create_request_context(self.user1)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data
        self.assertEqual(len(data["friends"]), 1)
        friend_ids = [friend["id"] for friend in data["friends"]]
        self.assertIn(self.user2.id, friend_ids)

        # friend's friend list visible
        context = self.create_request_context(self.user2)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data
        self.assertEqual(len(data["friends"]), 1)
        friend_ids = [friend["id"] for friend in data["friends"]]
        self.assertIn(self.user2.id, friend_ids)

        # others' friend list not visible
        context = self.create_request_context(self.user3)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data
        self.assertEqual(len(data["friends"]), 0)

    def test_serialize_tasks_only_visible_for_own_profile(self):
        task1 = Task.objects.create(created_by=self.user1, description="abc")
        task2 = Task.objects.create(created_by=self.user1, description="def")

        # tasks visible for own profile
        context = self.create_request_context(self.user1)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data
        self.assertEqual(len(data["tasks"]), 2)
        task_ids = [task["id"] for task in data["tasks"]]
        self.assertIn(task1.id, task_ids)
        self.assertIn(task2.id, task_ids)

        # other's tasks not visible
        context = self.create_request_context(self.user2)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data
        self.assertEqual(len(data["tasks"]), 0)

    def test_serialize_user_with_no_journals(self):
        context = self.create_request_context(self.user1)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data

        self.assertEqual(len(data["journal_entries"]), 0)

    def test_serialize_user_with_no_friends(self):
        context = self.create_request_context(self.user1)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data

        self.assertEqual(len(data["friends"]), 0)

    def test_serialize_user_with_no_tasks(self):
        context = self.create_request_context(self.user1)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data

        self.assertEqual(len(data["tasks"]), 0)

    def test_friends_serialized_as_mini_user_objects(self):
        self.user1.friends.add(self.user2)

        context = self.create_request_context(self.user1)
        serializer = UserSerializer(self.user1, context=context)
        data = serializer.data

        self.assertEqual(len(data["friends"]), 1)
        friend = data["friends"][0]
        self.assertIsInstance(friend, dict)
        self.assertEqual(len(friend.keys()), 4)
        self.assertIn("id", friend)
        self.assertIn("email", friend)
        self.assertIn("first_name", friend)
        self.assertIn("last_name", friend)
        self.assertNotIn("friends", friend)
        self.assertNotIn("journal_entries", friend)
        self.assertNotIn("tasks", friend)
        self.assertNotIn("clerk_id", friend)

