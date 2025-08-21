from rest_framework import serializers
from .models import JournalEntry, FriendRequest, CustomUser


class JournalEntrySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='journal-detail')
    created_at = serializers.ReadOnlyField()
    author = serializers.ReadOnlyField(source='author.username')
    shared_to = serializers.HyperlinkedRelatedField(many=True, queryset = CustomUser.objects.none(), view_name='customuser-detail', read_only=False, lookup_field="username")

    class Meta:
        model = JournalEntry
        fields = ['url', 'id', 'created_at', 'title', 'author', 'content', 'access', 'shared_to']

    # to share with others, show list of all users except current user
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            fields["shared_to"].child_relation.queryset = CustomUser.objects.exclude(id=request.user.id)
        return fields

    # show shared_to list only if curr user is author or in shared_to list
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            user = request.user
            if not ((instance.author == user or user in instance.shared_to.all()) and instance.access == "custom"):
                rep.pop("shared_to", None)
        return rep



class UserSerializer(serializers.HyperlinkedModelSerializer):
    friends = serializers.HyperlinkedRelatedField(many=True, view_name='customuser-detail', read_only=True, lookup_field = "username")
    journal_entries =  serializers.SerializerMethodField(method_name='get_journal_entries')

    class Meta:
        model = CustomUser
        fields = ('url', 'id', 'username', 'first_name', 'last_name', 'email', 'friends', 'journal_entries')
        extra_kwargs = {"url": {"view_name": "customuser-detail", "lookup_field": "username"}}

    # show all journal entries if own detail else show only public or entries shared with me
    def get_journal_entries(self, instance):
        request = self.context.get("request")
        user = request.user
        if instance == user:
            queryset = instance.journal_entries.all()
        else:
            queryset = (instance.journal_entries.filter(access="public")
                        .union(instance.journal_entries.filter(access="custom", shared_to=user)))
        field = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='journal-detail')
        field.bind('journal_entries', self)
        return field.to_representation(queryset)

    # show friends list only if own detail page or if curr user is in friends list
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get("request")
        user = request.user
        if not (instance == user or user in instance.friends.all()):
            rep.pop("friends", None)
        return rep



class FriendRequestSerializer(serializers.HyperlinkedModelSerializer):
    request_from = serializers.SlugRelatedField(source="requested_by",slug_field='username', read_only=True)
    request_to = serializers.SlugRelatedField(source="requested_to", queryset= CustomUser.objects.none(), slug_field='username', read_only=False)

    class Meta:
        model = FriendRequest
        fields = ['url', 'created_at', 'request_from', 'request_to', 'accepted']
        read_only_fields = ['created_at', 'request_from', 'accepted']

    # hide from the 'request to' menu when sending friend request -> curr user, users already in requests to/from me
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            user = request.user
            fields['request_to'].queryset = (CustomUser.objects
                                            .exclude(id=user.id)
                                            .exclude(id__in=FriendRequest.objects.filter(requested_by=user).values_list('requested_to_id', flat=True))
                                            .exclude(id__in=FriendRequest.objects.filter(requested_to=user).values_list('requested_by_id', flat=True)))
        return fields


class FriendshipAcceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ['accepted']
