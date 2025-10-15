""" tests for journals urls """

from django.test import TestCase
from django.urls import resolve, reverse
from journals import views


class JournalURLsTests(TestCase):
    """tests to ensure that journals app urls correctly resolve to their views"""

    def test_journal_list_create_is_resolved(self):
        """journal list url resolves to JournalEntryListCreateView"""
        url = reverse("journals:journal-list-create")
        self.assertEqual(url, "/journals/")
        self.assertEqual(resolve(url).func.view_class, views.JournalEntryListCreateView)

    def test_journal_detail_is_resolved(self):
        """journal detail url resolves to JournalEntryDetailView"""
        url = reverse("journals:journal-detail", args=[1])
        self.assertEqual(url, "/journals/1/")
        self.assertEqual(resolve(url).func.view_class, views.JournalEntryDetailView)

    def test_my_journals_is_resolved(self):
        """my journals url resolves to MyJournalsView"""
        url = reverse("journals:my-journals")
        self.assertEqual(url, "/journals/my-journals/")
        self.assertEqual(resolve(url).func.view_class, views.MyJournalsView)

    def test_shared_with_me_is_resolved(self):
        """shared with me url resolves to SharedWithMeView"""
        url = reverse("journals:shared-with-me")
        self.assertEqual(url, "/journals/shared-with-me/")
        self.assertEqual(resolve(url).func.view_class, views.SharedWithMeView)

    def test_public_journals_is_resolved(self):
        """public url resolves to PublicJournalsView"""
        url = reverse("journals:public-journals")
        self.assertEqual(url, "/journals/public/")
        self.assertEqual(resolve(url).func.view_class, views.PublicJournalsView)

    def test_task_delete_is_resolved(self):
        """task delete url resolves to TaskDeleteView"""
        url = reverse("task-delete", args=[1])
        self.assertEqual(url, "/tasks/1/")
        self.assertEqual(resolve(url).func.view_class, views.TaskDeleteView)
