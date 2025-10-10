from django.test import TestCase
from users.models import CustomUser
from ..models import JournalEntry, Task
from datetime import date
from django.db.utils import DataError


class JournalModelTests(TestCase):

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

    def test_journal_create_with_required_fields(self):
        journal = JournalEntry.objects.create(author=self.user1, content="abc")

        self.assertIsNotNone(journal.id)
        self.assertEqual(journal.author, self.user1)
        self.assertEqual(journal.content, "abc")
        self.assertEqual(journal.title, "")
        self.assertEqual(journal.access, "private")
        self.assertEqual(journal.created_at, date.today())

    def test_journal_creation_with_all_fields(self):
        journal = JournalEntry.objects.create(
            author=self.user1, title="abc", content="def", access="public"
        )
        self.assertEqual(journal.title, "abc")
        self.assertEqual(journal.access, "public")

    def test_journal_title_max_length(self):
        long_title = "a" * 101
        with self.assertRaises(DataError):
            JournalEntry.objects.create(
                author=self.user1, title=long_title, content="abc"
            )

    def test_journal_created_at_is_date(self):
        journal = JournalEntry.objects.create(author=self.user1, content="abc")
        self.assertIsInstance(journal.created_at, date)

    def test_journal_entries_by_an_author(self):
        JournalEntry.objects.create(author=self.user1, content="abc")
        JournalEntry.objects.create(author=self.user1, content="abc")
        JournalEntry.objects.create(author=self.user2, content="abc")

        self.assertEqual(self.user1.journal_entries.count(), 2)
        self.assertEqual(self.user2.journal_entries.count(), 1)

    def test_journal_access(self):
        private = JournalEntry.objects.create(
            author=self.user1, content="abc", access="private"
        )
        public = JournalEntry.objects.create(
            author=self.user1, content="abc", access="public"
        )
        custom = JournalEntry.objects.create(
            author=self.user1, content="abc", access="custom"
        )

        self.assertEqual(private.access, "private")
        self.assertEqual(public.access, "public")
        self.assertEqual(custom.access, "custom")

    def test_journal_shared_to(self):
        journal = JournalEntry.objects.create(
            author=self.user1, content="abc", access="custom"
        )
        self.assertEqual(journal.shared_to.count(), 0)

        journal.shared_to.add(self.user2)
        self.assertEqual(journal.shared_to.count(), 1)
        self.assertIn(self.user2, journal.shared_to.all())

        journal.shared_to.add(self.user3)
        self.assertEqual(journal.shared_to.count(), 2)
        self.assertIn(self.user3, journal.shared_to.all())

        journal.shared_to.clear()
        self.assertEqual(journal.shared_to.count(), 0)

    def test_journal_cascade_delete_on_author_delete(self):
        journal = JournalEntry.objects.create(author=self.user1, content="abc")
        journal_id = journal.id

        self.user1.delete()
        self.assertFalse(JournalEntry.objects.filter(id=journal_id).exists())


class TaskModelTests(TestCase):

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

    def test_task_creation_with_required_fields(self):
        task = Task.objects.create(created_by=self.user1, description="abc")

        self.assertIsNotNone(task.id)
        self.assertEqual(task.created_by, self.user1)
        self.assertEqual(task.description, "abc")
        self.assertEqual(task.created_at, date.today())

    def test_task_cascade_delete_on_creator_delete(self):
        task = Task.objects.create(created_by=self.user1, description="abc")
        task_id = task.id

        self.user1.delete()
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_tasks_by_a_user(self):
        Task.objects.create(created_by=self.user1, description="abc")
        Task.objects.create(created_by=self.user1, description="abc")
        Task.objects.create(created_by=self.user2, description="abc")

        self.assertEqual(self.user1.tasks.count(), 2)
        self.assertEqual(self.user2.tasks.count(), 1)

    def test_task_created_at_is_date(self):
        task = Task.objects.create(created_by=self.user1, description="abc")
        self.assertIsInstance(task.created_at, date)
