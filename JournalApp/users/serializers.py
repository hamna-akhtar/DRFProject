"""
users serializers
defines serializers for CustomUser model.
includes methods to serialize user's friends, journal entries, and tasks
depending on requestor's authorization.
"""

from rest_framework import serializers
from journals.serializers import JournalEntrySerializer, TaskSerializer
from .models import CustomUser
from .common_serializers import UserMiniSerializer


class UserSerializer(serializers.ModelSerializer):
    """serializer for CustomUser model"""

    friends = serializers.SerializerMethodField(method_name="get_friends")
    journal_entries = serializers.SerializerMethodField(
        method_name="get_journal_entries"
    )
    tasks = serializers.SerializerMethodField(method_name="get_tasks")

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "clerk_id",
            "first_name",
            "last_name",
            "email",
            "friends",
            "journal_entries",
            "tasks",
        )

    def get_journal_entries(self, instance):
        """
        show all journal entries if own detail else show only
        public or entries shared with me
        """
        request = self.context.get("request")
        user = request.user
        if instance == user:
            queryset = instance.journal_entries.all()
        else:
            queryset = instance.journal_entries.filter(access="public").union(
                instance.journal_entries.filter(access="custom", shared_to=user)
            )
        return JournalEntrySerializer(queryset, many=True, context=self.context).data

    def get_friends(self, instance):
        """
        only show friends list if own profile or
        current user is in that friend's list
        """
        request = self.context.get("request")
        user = request.user
        if not (instance == user or user in instance.friends.all()):
            return []
        return UserMiniSerializer(
            instance.friends.all(), many=True, context=self.context
        ).data

    def get_tasks(self, instance):
        """get all tasks for currently authenticated user"""
        request = self.context.get("request")
        user = request.user
        if not instance == user:
            return []
        return TaskSerializer(
            instance.tasks.all(), many=True, context=self.context
        ).data
