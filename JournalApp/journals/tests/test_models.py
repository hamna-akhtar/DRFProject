""" tests for journals models """

from datetime import date
from django.db.utils import DataError
from tests.base import CustomBaseTestCase
from journals.models import JournalEntry, Task


class JournalEntryModelTests(CustomBaseTestCase):
    """tests for JournalEntry model"""

    def test_journal_create_with_required_fields(self):
        """journal entry can be created with only author and content fields"""
        journal = JournalEntry.objects.create(author=self.user1, content="abc")

        self.assertIsNotNone(journal.id)
        self.assertEqual(journal.author, self.user1)
        self.assertEqual(journal.content, "abc")
        self.assertEqual(journal.title, "")
        self.assertEqual(journal.access, "private")
        self.assertEqual(journal.created_at, date.today())

    def test_journal_creation_with_all_fields(self):
        """journal entry can be created with all fields"""
        journal = JournalEntry.objects.create(
            author=self.user1, title="abc", content="def", access="public"
        )
        self.assertEqual(journal.title, "abc")
        self.assertEqual(journal.access, "public")

    def test_journal_title_max_length(self):
        """raise error on exceeding title max length"""
        long_title = "a" * 101
        with self.assertRaises(DataError):
            JournalEntry.objects.create(
                author=self.user1, title=long_title, content="abc"
            )

    def test_journal_created_at_is_date(self):
        """created_at is stored as a date object"""
        journal = JournalEntry.objects.create(author=self.user1, content="abc")
        self.assertIsInstance(journal.created_at, date)

    def test_journal_entries_by_an_author(self):
        """a user can create multiple journal entries"""
        JournalEntry.objects.create(author=self.user1, content="abc")
        JournalEntry.objects.create(author=self.user1, content="abc")
        JournalEntry.objects.create(author=self.user2, content="abc")

        self.assertEqual(self.user1.journal_entries.count(), 2)
        self.assertEqual(self.user2.journal_entries.count(), 1)

    def test_journal_access(self):
        """journal entry access can be public, private, custom"""
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
        """journal entry can be shared to other users"""
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
        """author deletion cascades to deletion of journal entries by that author"""
        journal1 = JournalEntry.objects.create(author=self.user1, content="abc")
        journal1_id = journal1.id

        journal2 = JournalEntry.objects.create(author=self.user1, content="abc")
        journal2_id = journal2.id

        self.user1.delete()
        self.assertFalse(JournalEntry.objects.filter(id=journal1_id).exists())
        self.assertFalse(JournalEntry.objects.filter(id=journal2_id).exists())


class TaskModelTests(CustomBaseTestCase):
    """tests for Task model"""

    def test_task_creation_with_required_fields(self):
        """task can be created with only created_by and description fields"""
        task = Task.objects.create(created_by=self.user1, description="abc")

        self.assertIsNotNone(task.id)
        self.assertEqual(task.created_by, self.user1)
        self.assertEqual(task.description, "abc")
        self.assertEqual(task.created_at, date.today())

    def test_task_cascade_delete_on_creator_delete(self):
        """user deletion cascades to deletion of user's tasks"""
        task = Task.objects.create(created_by=self.user1, description="abc")
        task_id = task.id

        self.user1.delete()
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_tasks_by_a_user(self):
        """a user can have multiple tasks"""
        Task.objects.create(created_by=self.user1, description="abc")
        Task.objects.create(created_by=self.user1, description="abc")
        Task.objects.create(created_by=self.user2, description="abc")

        self.assertEqual(self.user1.tasks.count(), 2)
        self.assertEqual(self.user2.tasks.count(), 1)

    def test_task_created_at_is_date(self):
        """task created_at is stored as a date object"""
        task = Task.objects.create(created_by=self.user1, description="abc")
        self.assertIsInstance(task.created_at, date)
