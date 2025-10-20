""" tests for journals views """

from datetime import date
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import force_authenticate
from tests.base import CustomBaseTestCase
from journals import views
from journals.models import JournalEntry, Task


class JournalEntryListCreateViewTests(CustomBaseTestCase):
    """tests for JournalEntryListCreateView"""

    def test_journal_list_create_requires_authentication(self):
        """only authenticated users can list/create journal entries"""
        view = views.JournalEntryListCreateView.as_view()
        request = self.factory.get("journals/")

        # without auth
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_journal_list_includes_my_shared_public(self):
        """journal entry list includes own, shared and public journals"""
        my = JournalEntry.objects.create(
            title="my", content="abc", author=self.user1, access="private"
        )
        public = JournalEntry.objects.create(
            title="public", content="abc", author=self.user2, access="public"
        )
        shared = JournalEntry.objects.create(
            title="shared", content="abc", author=self.user3, access="custom"
        )
        shared.shared_to.add(self.user1)

        request = self.factory.get("journals/")
        force_authenticate(request, user=self.user1)
        view = views.JournalEntryListCreateView.as_view()
        response = view(request)
        response.render()

        returned_ids = {journal["id"] for journal in response.data}
        self.assertIn(my.id, returned_ids)
        self.assertIn(public.id, returned_ids)
        self.assertIn(shared.id, returned_ids)

    @patch("journals.tasks.extract_and_create_tasks.delay")
    @patch(
        "journals.views.transaction.on_commit", new=lambda fn: fn()
    )  # run immediately
    def test_journal_create_sets_author_and_created_at(self, mock_extract):
        """set author, date, and create extracted tasks on journal entry creation"""
        mock_extract.return_value = {"status": "ok", "created_task_ids": [1, 2]}

        data = {"title": "title", "content": "abc", "access": "public", "shared_to": []}
        http_request = self.factory.post("journals/", data, format="json")
        force_authenticate(http_request, user=self.user1)
        view = views.JournalEntryListCreateView.as_view()
        response = view(http_request)
        response.render()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_journal = JournalEntry.objects.get(id=response.data["id"])
        self.assertEqual(new_journal.author, self.user1)
        self.assertEqual(new_journal.created_at, date.today())

    @patch("journals.tasks.extract_and_create_tasks.delay")
    @patch("journals.views.transaction.on_commit", new=lambda fn: fn())
    def test_journal_create_keeps_shared_to_if_custom_access_else_clears(
        self, mock_extract
    ):
        """preserve shared_to list for custom access journals only"""
        mock_extract.return_value = {"status": "ok", "created_task_ids": [1, 2]}
        view = views.JournalEntryListCreateView.as_view()

        # custom access
        data = {
            "title": "title",
            "content": "abc",
            "access": "custom",
            "shared_to": [self.user2.id],
        }
        http_request = self.factory.post("journals/", data, format="json")
        force_authenticate(http_request, user=self.user1)
        response = view(http_request)
        response.render()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_journal = JournalEntry.objects.get(id=response.data["id"])
        self.assertIn(self.user2, new_journal.shared_to.all())

        # public access
        data = {
            "title": "title",
            "content": "abc",
            "access": "public",
            "shared_to": [self.user2.id],
        }
        http_request = self.factory.post("journals/", data, format="json")
        force_authenticate(http_request, user=self.user1)
        response = view(http_request)
        response.render()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_journal = JournalEntry.objects.get(id=response.data["id"])
        self.assertEqual(new_journal.shared_to.count(), 0)

        # private access
        data = {
            "title": "title",
            "content": "abc",
            "access": "private",
            "shared_to": [self.user2.id],
        }
        http_request = self.factory.post("journals/", data, format="json")
        force_authenticate(http_request, user=self.user1)
        response = view(http_request)
        response.render()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_journal = JournalEntry.objects.get(id=response.data["id"])
        self.assertEqual(new_journal.shared_to.count(), 0)


class JournalEntryDetailViewTests(CustomBaseTestCase):
    """tests for JournalEntryDetailView"""

    def test_journal_retrieve_private_by_author_only(self):
        """private journal entry can be retrieved by author"""
        view = views.JournalEntryDetailView.as_view()
        journal = JournalEntry.objects.create(
            title="title", content="abc", author=self.user1, access="private"
        )
        request = self.factory.get(f"journals/{journal.id}")

        # retrieve by author
        force_authenticate(request, user=self.user1)
        response = view(request, pk=journal.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # retrieve by other user
        force_authenticate(request, user=self.user2)
        response = view(request, pk=journal.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_journal_retrieve_public_by_all(self):
        """public journal entry can be retrieved by all authenticated users"""
        view = views.JournalEntryDetailView.as_view()
        journal = JournalEntry.objects.create(
            title="title", content="abc", author=self.user1, access="public"
        )
        request = self.factory.get(f"journals/{journal.id}")

        # retrieve by author
        force_authenticate(request, user=self.user1)
        response = view(request, pk=journal.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # retrieve by other user
        force_authenticate(request, user=self.user2)
        response = view(request, pk=journal.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_journal_retrieve_custom_by_author_and_by_shared_to_only(self):
        """shared journal entry can be retrieved by author and shared user only"""
        view = views.JournalEntryDetailView.as_view()
        journal = JournalEntry.objects.create(
            title="title", content="abc", author=self.user1, access="custom"
        )
        journal.shared_to.add(self.user2)
        request = self.factory.get(f"journals/{journal.id}")

        # retrieve by author
        force_authenticate(request, user=self.user1)
        response = view(request, pk=journal.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # retrieve by shared to user
        force_authenticate(request, user=self.user2)
        response = view(request, pk=journal.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # retrieve by other user
        force_authenticate(request, user=self.user3)
        response = view(request, pk=journal.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("journals.tasks.extract_and_create_tasks.delay")
    @patch("journals.views.transaction.on_commit", new=lambda fn: fn())
    def test_journal_update_clears_shared_to_if_access_changed_from_custom(
        self, mock_extract
    ):
        """clear shared_to list if access is updated from custom to public/private"""
        mock_extract.return_value = {"status": "ok", "created_task_ids": [1, 2]}

        journal = JournalEntry.objects.create(
            title="initial", content="abc", author=self.user1, access="custom"
        )
        journal.shared_to.add(self.user2)
        self.assertEqual(journal.shared_to.count(), 1)

        data = {
            "title": "updated title",
            "content": "updated content",
            "access": "public",
        }
        request = self.factory.patch(f"journals/{journal.id}", data, format="json")
        force_authenticate(request, user=self.user1)
        view = views.JournalEntryDetailView.as_view()
        response = view(request, pk=journal.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(journal.shared_to.count(), 0)

    @patch("journals.tasks.extract_and_create_tasks.delay")
    @patch("journals.views.transaction.on_commit", new=lambda fn: fn())
    def test_journal_update_keeps_shared_to_if_access_changed_to_custom(
        self, mock_extract
    ):
        """preserve shared_to if access is updated from public/private to custom"""
        mock_extract.return_value = {"status": "ok", "created_task_ids": [1, 2]}

        journal = JournalEntry.objects.create(
            title="initial", content="abc", author=self.user1, access="private"
        )
        self.assertEqual(journal.shared_to.count(), 0)

        data = {
            "title": "updated title",
            "content": "updated content",
            "access": "custom",
            "shared_to": [self.user2.id],
        }
        request = self.factory.patch(f"journals/{journal.id}", data, format="json")
        force_authenticate(request, user=self.user1)
        view = views.JournalEntryDetailView.as_view()
        response = view(request, pk=journal.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(journal.shared_to.count(), 1)

    @patch("journals.tasks.extract_and_create_tasks.delay")
    @patch("journals.views.transaction.on_commit", new=lambda fn: fn())
    def test_journal_delete_by_author_only(self, mock_extract):
        """journal entry can be deleted by author only"""
        mock_extract.return_value = {"status": "ok", "created_task_ids": [1, 2]}

        view = views.JournalEntryDetailView.as_view()
        journal = JournalEntry.objects.create(
            title="initial", content="abc", author=self.user1, access="custom"
        )
        journal.shared_to.add(self.user2)
        request = self.factory.delete(f"journals/{journal.id}")

        # delete by other user
        force_authenticate(request, user=self.user3)
        response = view(request, pk=journal.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # delete by shared to user
        force_authenticate(request, user=self.user2)
        response = view(request, pk=journal.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # delete by author
        force_authenticate(request, user=self.user1)
        response = view(request, pk=journal.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class MyJournalsViewTests(CustomBaseTestCase):
    """tests for MyJournalsView"""

    def test_my_journals(self):
        """return only journals created by currently authenticated user"""
        user1_journal = JournalEntry.objects.create(
            title="user1 journal", content="abc", author=self.user1
        )
        user2_journal = JournalEntry.objects.create(
            title="user2 journal", content="abc", author=self.user2
        )
        request = self.factory.get("journals/my-journals")
        view = views.MyJournalsView.as_view()

        # user1's journals
        force_authenticate(request, user=self.user1)
        response = view(request)
        response.render()
        returned_ids = {item["id"] for item in response.data}
        self.assertEqual(len(returned_ids), 1)
        self.assertIn(user1_journal.id, returned_ids)
        self.assertNotIn(user2_journal.id, returned_ids)

        # user2's journals
        force_authenticate(request, user=self.user2)
        response = view(request)
        response.render()
        returned_ids = {item["id"] for item in response.data}
        self.assertEqual(len(returned_ids), 1)
        self.assertIn(user2_journal.id, returned_ids)
        self.assertNotIn(user1_journal.id, returned_ids)


class PublicJournalsViewTests(CustomBaseTestCase):
    """tests for PublicJournalsView"""

    def test_public_journals_shows_all_public_journals_except_own(self):
        """return all public journals except those created by currently authenticated user"""
        public_own = JournalEntry.objects.create(
            title="user1 public journal",
            content="abc",
            author=self.user1,
            access="public",
        )
        public_other = JournalEntry.objects.create(
            title="user2 public journal",
            content="abc",
            author=self.user2,
            access="public",
        )
        private = JournalEntry.objects.create(
            title="user1 private journal",
            content="abc",
            author=self.user1,
            access="private",
        )
        shared = JournalEntry.objects.create(
            title="user1 shared journal",
            content="abc",
            author=self.user1,
            access="custom",
        )

        request = self.factory.get("journals/public")
        view = views.PublicJournalsView.as_view()

        force_authenticate(request, user=self.user1)
        response = view(request)
        response.render()
        returned_ids = {item["id"] for item in response.data}

        self.assertEqual(len(returned_ids), 1)
        self.assertIn(public_other.id, returned_ids)

        self.assertNotIn(public_own.id, returned_ids)
        self.assertNotIn(private.id, returned_ids)
        self.assertNotIn(shared.id, returned_ids)


class SharedWithMeViewTests(CustomBaseTestCase):
    """tests for SharedWithMeView"""

    def test_shared_with_me_journals(self):
        """return only journals shared to currently authenticated user"""
        shared = JournalEntry.objects.create(
            title="user1 shared with user2",
            content="abc",
            author=self.user1,
            access="custom",
        )
        shared.shared_to.add(self.user2)
        private = JournalEntry.objects.create(
            title="user1 private journal",
            content="abc",
            author=self.user1,
            access="private",
        )
        public = JournalEntry.objects.create(
            title="user1 public journal",
            content="abc",
            author=self.user1,
            access="public",
        )

        request = self.factory.get("journals/shared-with-me/")
        view = views.SharedWithMeView.as_view()

        # user2's shared-with-me view
        force_authenticate(request, user=self.user2)
        response = view(request)
        response.render()
        returned_ids = {item["id"] for item in response.data}

        self.assertIn(shared.id, returned_ids)

        self.assertNotIn(private.id, returned_ids)
        self.assertNotIn(public.id, returned_ids)


class TaskDeleteViewTests(CustomBaseTestCase):
    """tests for TaskDeleteView"""

    def test_task_delete_by_creator_only(self):
        """task can only be deleted by user who created it"""
        view = views.TaskDeleteView.as_view()
        task = Task.objects.create(description="task to delete", created_by=self.user1)
        request = self.factory.delete(f"tasks/{task.id}")

        # delete request by other user
        force_authenticate(request, user=self.user2)
        response = view(request, pk=task.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # delete request by user who created task
        force_authenticate(request, user=self.user1)
        response = view(request, pk=task.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
