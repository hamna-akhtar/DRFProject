from rest_framework import serializers
from .models import JournalEntry
from users.models import CustomUser
from users.common_serializers import UserMiniSerializer


class JournalEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = JournalEntry

    created_at = serializers.ReadOnlyField()
    author = UserMiniSerializer(read_only=True)
    shared_to = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.none(), many=True, write_only=True)

    class Meta:
        model = JournalEntry
        fields = [ 'id', 'created_at', 'title', 'author', 'content', 'access', 'shared_to']

    # to share with others, show list of all users except current user
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            fields["shared_to"].child_relation.queryset = CustomUser.objects.exclude(id=request.user.id)
        return fields

    # show shared_to list only if curr user is author or in shared_to list
    def to_representation(self, instance):
        request = self.context.get("request")
        rep = super().to_representation(instance)

        if request and request.user.is_authenticated:
            user = request.user
            if not ((instance.author == user or user in instance.shared_to.all()) and instance.access == "custom"):
                rep.pop("shared_to", None)
            else:
                # nested data for reads
                rep["shared_to"] = UserMiniSerializer(instance.shared_to.all(), many=True, context=self.context).data
        return rep


