from .models import JournalEntry, Task
from .serializers import JournalEntrySerializer, TaskSerializer
from .utils import extract_action_items
from rest_framework import generics
from .permissions import JournalPermission
from rest_framework import permissions
from datetime import datetime


class TaskDeleteView(generics.DestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(created_by=self.request.user)



class JournalEntryListCreateView(generics.ListCreateAPIView):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated, JournalPermission]

    def get_queryset(self):
        user = self.request.user
        my_journals = JournalEntry.objects.filter(author=user)
        public_journals = JournalEntry.objects.filter(access="public").exclude(author=user)
        shared_with_me = JournalEntry.objects.filter(shared_to=user)

        return (my_journals | public_journals | shared_with_me).distinct()

    def perform_create(self, serializer):
        access = self.request.data.get("access")
        if access == "custom":
            journal = serializer.save(author=self.request.user, created_at=datetime.today())
        else:
           journal = serializer.save(author=self.request.user, created_at=datetime.today(), shared_to=[])

        new_tasks = extract_action_items(journal.content)
        for task_desc in new_tasks:
            if not Task.objects.filter(created_by=self.request.user, description=task_desc.strip()).exists():
                Task.objects.create(created_by=self.request.user, description=task_desc.strip())


class JournalEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated, JournalPermission]
    queryset = JournalEntry.objects.all()

    # if access changed from custom to something else, then empty shared_to list
    def perform_update(self, serializer):
        access = self.request.data.get("access")
        journal = serializer.save()
        if access != "custom":
            journal.shared_to.clear()

        new_tasks = extract_action_items(journal.content)
        for task_desc in new_tasks:
            if not Task.objects.filter(created_by=self.request.user, description=task_desc.strip()).exists():
                Task.objects.create(created_by=self.request.user, description=task_desc.strip())



class MyJournalsView(generics.ListAPIView):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        my_journals = JournalEntry.objects.filter(author=self.request.user)
        return my_journals



class SharedWithMeView(generics.ListAPIView):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        shared = JournalEntry.objects.all().filter(shared_to=self.request.user)
        return shared



class PublicJournalsView(generics.ListAPIView):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        public = JournalEntry.objects.all().filter(access='public').exclude(author=self.request.user)
        return public