from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import CustomUser
from journals.serializers import JournalEntrySerializer
from .common_serializers import UserMiniSerializer


class UserSerializer(serializers.ModelSerializer):
    friends = serializers.SerializerMethodField(method_name='get_friends')
    journal_entries =  serializers.SerializerMethodField(method_name='get_journal_entries')

    class Meta:
        model = CustomUser
        fields = ('id', 'clerk_id', 'first_name', 'last_name', 'email', 'friends', 'journal_entries')

    # show all journal entries if own detail else show only public or entries shared with me
    def get_journal_entries(self, instance):
        request = self.context.get("request")
        user = request.user
        if instance == user:
            queryset = instance.journal_entries.all()
        else:
            queryset = (
                instance.journal_entries.filter(access="public")
                .union(instance.journal_entries.filter(access="custom", shared_to=user))
            )
        return JournalEntrySerializer(queryset, many=True, context=self.context).data


    # only show friends list if own profile or current user is in that friend's list
    def get_friends(self, instance):
        request = self.context.get("request")
        user = request.user
        if not (instance == user or user in instance.friends.all()):
            return []
        return UserMiniSerializer(instance.friends.all(), many=True, context=self.context).data
