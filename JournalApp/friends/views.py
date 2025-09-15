from .models import FriendRequest
from .serializers import  FriendRequestSerializer, FriendAcceptSerializer
from rest_framework import generics
from .permissions import IsRequesterOrReceiverOrCreateOnly
from rest_framework import permissions
from datetime import datetime



class FriendRequestListCreateView(generics.ListCreateAPIView):
    # create anyone, view & list and destroy only requested_by or requested_to, accept only receiver
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsRequesterOrReceiverOrCreateOnly]

    def get_queryset(self):
        user = self.request.user
        sent = FriendRequest.objects.all().filter(requested_by=user)
        received = FriendRequest.objects.all().filter(requested_to=user)

        return (sent | received ).distinct()

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user, created_at=datetime.today())



class FriendRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsRequesterOrReceiverOrCreateOnly]
    queryset = FriendRequest.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return FriendAcceptSerializer
        return FriendRequestSerializer

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


class RequestsSentView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsRequesterOrReceiverOrCreateOnly]

    def get_queryset(self):
        sent = FriendRequest.objects.all().filter(requested_by=self.request.user).filter(accepted=False)
        return sent


class RequestsReceivedView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsRequesterOrReceiverOrCreateOnly]

    def get_queryset(self):
        received = FriendRequest.objects.all().filter(requested_to=self.request.user).filter(accepted=False)
        return received
