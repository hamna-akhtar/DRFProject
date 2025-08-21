from rest_framework.decorators import action
from rest_framework.response import Response
from .models import JournalEntry, FriendRequest, CustomUser
from .serializers import JournalEntrySerializer, FriendRequestSerializer, UserSerializer, FriendshipAcceptSerializer
from rest_framework import mixins
from .permissions import JournalPermission, IsSelfOrReadOnly, IsRequesterOrReceiverOrCreateOnly
from rest_framework import renderers, viewsets, permissions
from datetime import datetime


class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelfOrReadOnly]
    lookup_field = "username"


class JournalEntryViewSet(viewsets.ModelViewSet):
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
            serializer.save(author=self.request.user, created_at=datetime.today())
        else:
            serializer.save(author=self.request.user, created_at=datetime.today(), shared_to=[])

    # if access changed from custom to something else, then empty shared_to list
    def perform_update(self, serializer):
        access = self.request.data.get("access")
        journal = serializer.save()
        if access != "custom":
            journal.shared_to.clear()

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def my_journals(self, request, pk=None):
        shared = JournalEntry.objects.all().filter(author=request.user)
        serializer = self.get_serializer(shared, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def shared_with_me(self, request, pk=None):
        shared = JournalEntry.objects.all().filter(shared_to=request.user)
        serializer = self.get_serializer(shared, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def public_journals(self, request, pk=None):
        public = JournalEntry.objects.all().filter(access='public').exclude(author=request.user)
        serializer = self.get_serializer(public, many=True)
        return Response(serializer.data)



class FriendRequestViewSet(viewsets.ModelViewSet):
    # create anyone, view & list and destroy only requested_by or requested_to, accept only receiver
    permission_classes = [permissions.IsAuthenticated, IsRequesterOrReceiverOrCreateOnly]

    def get_queryset(self):
        user = self.request.user
        sent = FriendRequest.objects.all().filter(requested_by=user)
        received = FriendRequest.objects.all().filter(requested_to=user)

        return (sent | received ).distinct()

    def get_serializer_class(self):
        if self.action in ['partial_update', 'update']:
            return FriendshipAcceptSerializer
        return FriendRequestSerializer

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user, created_at=datetime.today())

    def perform_update(self, serializer):
        friendship_request = serializer.save()

        if friendship_request:
            requester = friendship_request.requested_by
            receiver = friendship_request.requested_to

            if friendship_request.accepted:
                # Add to each other's friends lists only if not already added
                if receiver not in requester.friends.all():
                    requester.friends.add(receiver)
            else:
                # Remove from each other's friends lists if the request is unaccepted
                if receiver in requester.friends.all():
                    requester.friends.remove(receiver)

    def perform_destroy(self, instance):
        requester = instance.requested_by
        receiver = instance.requested_to
        # if friends, remove them from each other's friends lists
        if instance.accepted:
                requester.friends.remove(receiver)
        instance.delete()

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def requests_sent(self, request, pk=None):
        sent = FriendRequest.objects.all().filter(requested_by=request.user)
        serializer = self.get_serializer(sent, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def requests_received(self, request, pk=None):
        received = FriendRequest.objects.all().filter(requested_to=request.user)
        serializer = self.get_serializer(received, many=True)
        return Response(serializer.data)
