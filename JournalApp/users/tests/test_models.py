""" tests for users models """

from django.test import TestCase
from journals.models import JournalEntry, Task
from users.models import CustomUser


class CustomUserModelTests(TestCase):
    """tests for custom user model"""

    def test_user_creation_with_email_only(self):
        """user can be created with email and password only"""
        user = CustomUser.objects.create(email="user@gmail.com", password="abcdef")
        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, "user@gmail.com")
        self.assertIsNone(user.clerk_id)
        self.assertIsNone(user.username)

    def test_user_creation_with_all_fields(self):
        """user can be created with all fields"""
        user = CustomUser.objects.create(
            email="user@gmail.com",
            password="abcdef",
            clerk_id="123456",
            username="user",
            first_name="ben",
            last_name="adams",
        )
        self.assertEqual(user.clerk_id, "123456")
        self.assertEqual(user.username, "user")
        self.assertEqual(user.first_name, "ben")
        self.assertEqual(user.last_name, "adams")

    def test_email_is_username_field(self):
        """email field is used as username field for authentication"""
        self.assertEqual(CustomUser.USERNAME_FIELD, "email")

    def test_email_is_unique(self):
        """duplicate email addresses are not allowed"""
        CustomUser.objects.create(email="user@gmail.com", password="abcdef")
        with self.assertRaises(Exception):
            CustomUser.objects.create(email="user@gmail.com", password="abcdef")

    def test_clerk_id_is_unique(self):
        """duplicate clerk_id fields are not allowed"""
        CustomUser.objects.create(
            email="user1@gmail.com", clerk_id="123456", password="abcdef"
        )

        with self.assertRaises(Exception):
            CustomUser.objects.create(
                email="user2@gmail.com", clerk_id="123456", password="abcdef"
            )

    def test_username_not_unique(self):
        """usernames do not need to be distinct"""
        user1 = CustomUser.objects.create(
            email="user1@gmail.com", username="user1", password="abcdef"
        )
        user2 = CustomUser.objects.create(
            email="user2@gmail.com", username="user1", password="ghijkl"
        )
        self.assertEqual(user1.username, user2.username)

    def test_add_user_in_friends(self):
        """user can have multiple friends"""
        user1 = CustomUser.objects.create(email="user1@gmail.com", password="abcdef")
        user2 = CustomUser.objects.create(email="user2@gmail.com", password="ghijkl")
        user3 = CustomUser.objects.create(email="user3@gmail.com", password="mnopqr")
        self.assertEqual(user1.friends.count(), 0)
        user1.friends.add(user2)

        self.assertEqual(user1.friends.count(), 1)
        self.assertIn(user2, user1.friends.all())

        user1.friends.add(user3)
        self.assertEqual(user1.friends.count(), 2)
        self.assertIn(user3, user1.friends.all())

    def test_friends_is_symmetrical(self):
        """friends relationship is symmetrical between users"""
        user1 = CustomUser.objects.create(email="user1@gmail.com", password="abcdef")
        user2 = CustomUser.objects.create(email="user2@gmail.com", password="ghijkl")

        user1.friends.add(user2)
        self.assertIn(user2, user1.friends.all())
        self.assertIn(user1, user2.friends.all())

    def test_user_journal_entries(self):
        """user can have multiple journal entries"""
        user = CustomUser.objects.create(email="user@gmail.com", password="abcdef")
        JournalEntry.objects.create(author=user, content="abc")
        JournalEntry.objects.create(author=user, content="def")

        self.assertEqual(user.journal_entries.count(), 2)

    def test_user_tasks(self):
        """user can have multiple tasks"""
        user = CustomUser.objects.create(email="user@gmail.com", password="abcdef")
        Task.objects.create(created_by=user, description="abc")
        Task.objects.create(created_by=user, description="def")

        self.assertEqual(user.tasks.count(), 2)

    def test_user_deletion_cascades_journals_deletion(self):
        """deleting a user cascades deletion of related journal entries"""
        user = CustomUser.objects.create(email="user@gmail.com", password="abcdef")
        journal = JournalEntry.objects.create(author=user, content="abc")
        journal_id = journal.id

        user.delete()
        self.assertFalse(JournalEntry.objects.filter(id=journal_id).exists())

    def test_user_deletion_cascades_tasks_deletion(self):
        """deleting a user cascades deletion of related tasks"""
        user = CustomUser.objects.create(email="user@gmail.com", password="abcdef")
        task = Task.objects.create(created_by=user, description="abc")
        task_id = task.id

        user.delete()
        self.assertFalse(Task.objects.filter(id=task_id).exists())
