""" journals views """

from datetime import datetime
from rest_framework import permissions
from rest_framework import generics
from .models import JournalEntry, Task
from .serializers import JournalEntrySerializer, TaskSerializer
from .utils import extract_action_items
from .permissions import JournalPermission


class TaskDeleteView(generics.DestroyAPIView):
    """delete a task"""

    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """restrict queryset to tasks by currently authenticated user only"""
        return Task.objects.filter(created_by=self.request.user)


class JournalEntryListCreateView(generics.ListCreateAPIView):
    """list and create journal entry"""

    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated, JournalPermission]

    def get_queryset(self):
        """include my, shared, public journals in queryset"""
        user = self.request.user
        my_journals = JournalEntry.objects.filter(author=user)
        public_journals = JournalEntry.objects.filter(access="public").exclude(
            author=user
        )
        shared_with_me = JournalEntry.objects.filter(shared_to=user)

        return (my_journals | public_journals | shared_with_me).distinct()

    def perform_create(self, serializer):
        """save new journal entry with shared_to if access is custom,
        else empty shared_to.
        extract and create tasks from it
        """
        access = self.request.data.get("access")
        if access == "custom":
            journal = serializer.save(
                author=self.request.user, created_at=datetime.today()
            )
        else:
            journal = serializer.save(
                author=self.request.user, created_at=datetime.today(), shared_to=[]
            )

        new_tasks = extract_action_items(journal.content)
        for task_desc in new_tasks:
            desc = task_desc.strip()
            if (
                desc
                and desc != "None"
                and not Task.objects.filter(
                    created_by=self.request.user, description=desc
                ).exists()
            ):
                Task.objects.create(created_by=self.request.user, description=desc)


class JournalEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """journal entry detail, update and delete"""

    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated, JournalPermission]
    queryset = JournalEntry.objects.all()

    def perform_update(self, serializer):
        """if access changed from custom, then empty shared_to list"""
        access = self.request.data.get("access")
        journal = serializer.save()
        if access != "custom":
            journal.shared_to.clear()

        new_tasks = extract_action_items(journal.content)
        for task_desc in new_tasks:
            desc = task_desc.strip()
            if (
                desc
                and desc != "None"
                and not Task.objects.filter(
                    created_by=self.request.user, description=desc
                ).exists()
            ):
                Task.objects.create(created_by=self.request.user, description=desc)


class MyJournalsView(generics.ListAPIView):
    """my journals list"""

    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """only journals created by currently authenticated user are included in queryset"""
        my_journals = JournalEntry.objects.filter(author=self.request.user)
        return my_journals


class SharedWithMeView(generics.ListAPIView):
    """shared journals list"""

    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """only journals shared to currently authenticated user are included in queryset"""
        shared = JournalEntry.objects.all().filter(shared_to=self.request.user)
        return shared


class PublicJournalsView(generics.ListAPIView):
    """public journals list"""

    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """only journals with public access are included in queryset"""
        public = (
            JournalEntry.objects.all()
            .filter(access="public")
            .exclude(author=self.request.user)
        )
        return public
