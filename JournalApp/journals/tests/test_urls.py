from django.test import TestCase
from django.urls import resolve, reverse
from .. import views

class JournalURLsTests(TestCase):

    def test_journal_list_create_is_resolved(self):
        url = reverse("journals:journal-list-create")
        self.assertEqual(url, "/journals/")
        self.assertEqual(resolve(url).func.view_class, views.JournalEntryListCreateView)

    def test_journal_detail_is_resolved(self):
        url = reverse("journals:journal-detail", args=[1])
        self.assertEqual(url, "/journals/1/")
        self.assertEqual(resolve(url).func.view_class, views.JournalEntryDetailView)

    def test_my_journals_is_resolved(self):
        url = reverse("journals:my-journals")
        self.assertEqual(url, "/journals/my-journals/")
        self.assertEqual(resolve(url).func.view_class, views.MyJournalsView)

    def test_shared_with_me_is_resolved(self):
        url = reverse("journals:shared-with-me")
        self.assertEqual(url, "/journals/shared-with-me/")
        self.assertEqual(resolve(url).func.view_class, views.SharedWithMeView)

    def test_public_journals_is_resolved(self):
        url = reverse("journals:public-journals")
        self.assertEqual(url, "/journals/public/")
        self.assertEqual(resolve(url).func.view_class, views.PublicJournalsView)

    def test_task_delete_is_resolved(self):
        url = reverse("task-delete",  args=[1])
        self.assertEqual(url, "/tasks/1/")
        self.assertEqual(resolve(url).func.view_class, views.TaskDeleteView)

