""" journals serializers
define serializers for JournalEntry and Task models.
includes methods to serialize journal's shared_to list depending on
requestor's authorization.
"""

from rest_framework import serializers
from users.models import CustomUser
from users.common_serializers import UserMiniSerializer
from .models import JournalEntry, Task


class JournalEntrySerializer(serializers.ModelSerializer):
    """ " serializer for journal entry data with nested relationships"""

    created_at = serializers.ReadOnlyField()
    author = UserMiniSerializer(read_only=True)
    shared_to = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.none(), many=True, write_only=True
    )
    tasks = serializers.SerializerMethodField(method_name="get_tasks")

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "created_at",
            "title",
            "author",
            "content",
            "access",
            "shared_to",
            "tasks",
        ]

    def get_fields(self):
        """to share with others, show list of all users except current user"""
        fields = super().get_fields()
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            fields["shared_to"].child_relation.queryset = CustomUser.objects.exclude(
                id=request.user.id
            )
        return fields

    def to_representation(self, instance):
        """show shared_to list only if curr user is author or in shared_to list"""
        request = self.context.get("request")
        rep = super().to_representation(instance)

        if request and request.user.is_authenticated:
            user = request.user
            if not (
                (instance.author == user or user in instance.shared_to.all())
                and instance.access == "custom"
            ):
                rep.pop("shared_to", None)
            else:
                # nested data for reads
                rep["shared_to"] = UserMiniSerializer(
                    instance.shared_to.all(), many=True, context=self.context
                ).data
        return rep

    def get_tasks(self, instance):
        # only show related tasks if author of journal
        user = self.context.get("request").user
        if user == instance.author:
            return TaskSerializer(
                instance.tasks.all(), many=True, context=self.context
            ).data
        return []


class TaskSerializer(serializers.ModelSerializer):
    """serializer for Task model"""

    created_by = UserMiniSerializer(read_only=True)
    created_at = serializers.ReadOnlyField()

    class Meta:
        model = Task
        fields = ["id", "created_at", "created_by", "description", "from_journal"]
