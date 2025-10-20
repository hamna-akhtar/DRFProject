""" tests for journals serializers """

from datetime import date
from tests.base import CustomBaseTestCase
from journals.models import JournalEntry, Task
from journals.serializers import JournalEntrySerializer, TaskSerializer


class JournalSerializerTests(CustomBaseTestCase):
    """tests for JournalEntrySerializer"""

    def test_serialize_journal_basic_fields(self):
        """correctly serialize basic fields of a journal entry"""
        journal = JournalEntry.objects.create(
            author=self.user1,
            title="abc",
            content="def",
            access="private",
        )

        context = self.create_request_context(self.user1)
        serializer = JournalEntrySerializer(journal, context=context)
        data = serializer.data

        self.assertEqual(data["id"], journal.id)
        self.assertEqual(data["title"], "abc")
        self.assertEqual(data["content"], "def")
        self.assertEqual(data["access"], "private")
        self.assertEqual(data["created_at"], date.today())

    def test_serialize_author_as_nested_user_mini_object(self):
        """serialize author as user mini object"""
        journal = JournalEntry.objects.create(
            author=self.user1,
            title="abc",
            content="def",
            access="private",
        )

        context = self.create_request_context(self.user1)
        serializer = JournalEntrySerializer(journal, context=context)
        data = serializer.data

        self.assertIn("author", data)
        self.assertIsInstance(data["author"], dict)
        self.assertEqual(len(data["author"].keys()), 4)
        self.assertEqual(data["author"]["id"], self.user1.id)
        self.assertEqual(data["author"]["email"], self.user1.email)
        self.assertEqual(data["author"]["first_name"], self.user1.first_name)
        self.assertEqual(data["author"]["last_name"], self.user1.last_name)

    def test_serialize_shared_to_as_nested_objects_for_read(self):
        """serialize shared_to as nested objects"""
        journal = JournalEntry.objects.create(
            author=self.user1, content="abc", access="custom"
        )
        journal.shared_to.add(self.user2, self.user3)

        context = self.create_request_context(self.user1)
        serializer = JournalEntrySerializer(journal, context=context)
        data = serializer.data

        self.assertIn("shared_to", data)

        self.assertIsInstance(data["shared_to"][0], dict)
        self.assertEqual(len(data["author"].keys()), 4)

        self.assertIsInstance(data["shared_to"][1], dict)
        self.assertEqual(len(data["author"].keys()), 4)

    def test_serialize_shared_to_only_visible_to_author_and_shared_user(self):
        """shared_to field is only visible to author and shared user"""
        journal = JournalEntry.objects.create(
            author=self.user1, title="abc", content="def", access="custom"
        )
        journal.shared_to.add(self.user2)

        # shared_to list is visible to author
        context = self.create_request_context(self.user1)
        serializer = JournalEntrySerializer(journal, context=context)
        data = serializer.data
        self.assertIn("shared_to", data)
        self.assertEqual(data["shared_to"][0]["id"], self.user2.id)

        # shared_to list is visible to shared user
        context = self.create_request_context(self.user2)
        serializer = JournalEntrySerializer(journal, context=context)
        data = serializer.data
        self.assertIn("shared_to", data)
        self.assertEqual(data["shared_to"][0]["id"], self.user2.id)

        # shared_to list is not visible to any other user
        context = self.create_request_context(self.user3)
        serializer = JournalEntrySerializer(journal, context=context)
        data = serializer.data
        self.assertNotIn("shared_to", data)

    def test_serialize_shared_to_hidden_for_non_custom_access(self):
        """shared_to field is not visible for public and private access"""
        public = JournalEntry.objects.create(
            author=self.user1, content="abc", access="public"
        )
        private = JournalEntry.objects.create(
            author=self.user1, content="abc", access="private"
        )
        public.shared_to.add(self.user2)

        # shared_to not visible when public access
        context = self.create_request_context(self.user1)
        serializer = JournalEntrySerializer(public, context=context)
        data = serializer.data
        self.assertNotIn("shared_to", data)

        # shared_to not visible when private access
        serializer = JournalEntrySerializer(private, context=context)
        data = serializer.data
        self.assertNotIn("shared_to", data)

    def test_serialize_created_at_is_read_only(self):
        """created_at is read only field"""
        journal = JournalEntry.objects.create(
            author=self.user1, title="abc", content="def", access="public"
        )
        context = self.create_request_context(self.user1)
        serializer = JournalEntrySerializer(journal, context=context)

        self.assertTrue(serializer.fields["created_at"].read_only)

    def test_deserialize_valid_private_journal(self):
        """deserialize valid private journal entry data"""
        context = self.create_request_context(self.user1)
        data = {"title": "abc", "content": "def", "access": "private", "shared_to": []}

        serializer = JournalEntrySerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["title"], "abc")
        self.assertEqual(serializer.validated_data["content"], "def")
        self.assertEqual(serializer.validated_data["access"], "private")

    def test_deserialize_valid_custom_journal_with_shared_to(self):
        """deserialize valid shared journal entry data"""
        context = self.create_request_context(self.user1)
        data = {
            "title": "abc",
            "content": "def",
            "access": "custom",
            "shared_to": [self.user2.id, self.user3.id],
        }

        serializer = JournalEntrySerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data["shared_to"]), 2)

    def test_deserialize_shared_to_queryset_excludes_current_user(self):
        """shared_to queryset excludes currently authenticated user"""
        context = self.create_request_context(self.user1)
        serializer = JournalEntrySerializer(context=context)

        fields = serializer.get_fields()
        shared_to_field = fields["shared_to"]
        queryset = shared_to_field.child_relation.queryset

        # queryset excludes user1 but includes all others
        self.assertNotIn(self.user1, queryset)
        self.assertIn(self.user2, queryset)
        self.assertIn(self.user3, queryset)

    def test_deserialize_invalid_access_choice(self):
        """reject invalid access choice during deserialization"""
        context = self.create_request_context(self.user1)
        data = {"title": "abc", "content": "def", "access": "invalid", "shared_to": []}

        serializer = JournalEntrySerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("access", serializer.errors)

    def test_deserialize_content_required(self):
        """content field is required for deserializing"""
        context = self.create_request_context(self.user1)
        data = {
            "title": "abc",
            "access": "private",
            "shared_to": [],
        }

        serializer = JournalEntrySerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("content", serializer.errors)

    def test_deserialize_title_optional(self):
        """title field is optional for deserializing"""
        context = self.create_request_context(self.user1)
        data = {
            "content": "abc",
            "access": "private",
            "shared_to": [],
        }

        serializer = JournalEntrySerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())

    def test_deserialize_invalid_shared_to_user_ids(self):
        """reject invalid shared to users"""
        context = self.create_request_context(self.user1)
        data = {
            "title": "abc",
            "content": "def",
            "access": "custom",
            "shared_to": [99999],
        }

        serializer = JournalEntrySerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("shared_to", serializer.errors)

    def test_update_journal(self):
        """journal entry title, content, access and shared_to list can all be updated by author"""
        journal = JournalEntry.objects.create(
            author=self.user1, title="old", content="abc", access="private"
        )

        context = self.create_request_context(self.user1)
        data = {"title": "new", "content": "def", "access": "public", "shared_to": []}

        serializer = JournalEntrySerializer(
            journal, data=data, context=context, partial=False
        )
        self.assertTrue(serializer.is_valid())
        updated_journal = serializer.save()
        self.assertEqual(updated_journal.title, "new")
        self.assertEqual(updated_journal.content, "def")

    def test_partial_update_journal(self):
        """partial update of journal entry can be done by author"""
        journal = JournalEntry.objects.create(
            author=self.user1, title="old", content="abc", access="private"
        )

        context = self.create_request_context(self.user1)
        data = {"title": "new"}

        serializer = JournalEntrySerializer(
            journal, data=data, context=context, partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_journal = serializer.save()
        self.assertEqual(updated_journal.title, "new")
        self.assertEqual(updated_journal.content, "abc")


class TaskSerializerTests(CustomBaseTestCase):
    """tests for TaskSerializer"""

    def test_serialize_task_basic_fields(self):
        """correctly serialize basic fields of a task"""
        task = Task.objects.create(created_by=self.user1, description="abc")

        context = self.create_request_context(self.user1)
        serializer = TaskSerializer(task, context=context)
        data = serializer.data

        self.assertEqual(data["id"], task.id)
        self.assertEqual(data["description"], "abc")
        self.assertEqual(data["created_at"], date.today())

    def test_serialize_created_by_as_nested_object(self):
        """serialize created by as a nested object"""
        task = Task.objects.create(created_by=self.user1, description="abc")

        context = self.create_request_context(self.user1)
        serializer = TaskSerializer(task, context=context)
        data = serializer.data

        self.assertIn("created_by", data)
        self.assertIsInstance(data["created_by"], dict)

    def test_serialize_created_by_and_created_at_are_read_only(self):
        """serialize created_by and created_at as read only"""
        task = Task.objects.create(created_by=self.user1, description="abc")
        context = self.create_request_context(self.user1)
        serializer = TaskSerializer(task, context=context)

        self.assertTrue(serializer.fields["created_at"].read_only)
        self.assertTrue(serializer.fields["created_by"].read_only)

    def test_deserialize_valid_task(self):
        """deserialize valid task data"""
        context = self.create_request_context(self.user1)
        data = {"description": "abc"}

        serializer = TaskSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["description"], "abc")

    def test_deserialize_description_required(self):
        """description field is required for deserializing"""
        context = self.create_request_context(self.user1)
        # no description is invalid
        data = {}

        serializer = TaskSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("description", serializer.errors)

        # empty description is invalid
        data = {"description": ""}
        serializer = TaskSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("description", serializer.errors)

    def test_update_task_description(self):
        """update task's description field"""
        task = Task.objects.create(created_by=self.user1, description="old")

        context = self.create_request_context(self.user1)
        data = {"description": "new"}

        serializer = TaskSerializer(task, data=data, context=context)
        self.assertTrue(serializer.is_valid())
        updated_task = serializer.save()
        self.assertEqual(updated_task.description, "new")

    def test_serialize_multiple_tasks(self):
        """serialize multiple tasks correctly"""
        Task.objects.create(created_by=self.user1, description="task 1")
        Task.objects.create(created_by=self.user1, description="task 2")
        Task.objects.create(created_by=self.user1, description="task 3")

        tasks = Task.objects.all()
        context = self.create_request_context(self.user1)
        serializer = TaskSerializer(tasks, many=True, context=context)

        self.assertEqual(len(serializer.data), 3)
        descriptions = [task["description"] for task in serializer.data]
        self.assertIn("task 1", descriptions)
        self.assertIn("task 2", descriptions)
        self.assertIn("task 3", descriptions)
