""" friends views """

from datetime import datetime
from rest_framework import permissions
from rest_framework import generics
from chat.tasks import update_vector_store_for_user
from .models import FriendRequest
from .serializers import FriendRequestSerializer, FriendAcceptSerializer
from .permissions import IsRequesterOrReceiverOrCreateOnly


class FriendRequestListCreateView(generics.ListCreateAPIView):
    """list and create friend requests"""

    # create anyone, view & list and destroy only requested_by or requested_to, accept only receiver
    serializer_class = FriendRequestSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsRequesterOrReceiverOrCreateOnly,
    ]

    def get_queryset(self):
        """restrict queryset to friend requests to/from currently authenticated user"""
        user = self.request.user
        sent = FriendRequest.objects.all().filter(requested_by=user)
        received = FriendRequest.objects.all().filter(requested_to=user)

        return (sent | received).distinct()

    def perform_create(self, serializer):
        """set the requester and creation date when creating new friend request"""
        friend_request = serializer.save(
            requested_by=self.request.user, created_at=datetime.today()
        )

        # add request entry in both vector stores
        page_content = (
            f"Unaccepted Friend Request, sent to: {friend_request.requested_to}"
        )
        metadata = {"type": "sent friend request", "id": str(friend_request.id)}
        update_vector_store_for_user.delay(
            friend_request.requested_by.id,
            page_content=page_content,
            metadata=metadata,
            action="create",
        )

        page_content = (
            f"Unaccepted Friend Request, received from: {friend_request.requested_by}"
        )
        metadata = {"type": "received friend request", "id": str(friend_request.id)}
        update_vector_store_for_user.delay(
            friend_request.requested_to.id,
            page_content=page_content,
            metadata=metadata,
            action="create",
        )


class FriendRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """retrieve, update and delete friend requests"""

    permission_classes = [
        permissions.IsAuthenticated,
        IsRequesterOrReceiverOrCreateOnly,
    ]
    queryset = FriendRequest.objects.all()

    def get_serializer_class(self):
        """return serializer class based on request method"""
        if self.request.method in ["PUT", "PATCH"]:
            return FriendAcceptSerializer
        return FriendRequestSerializer

    def perform_update(self, serializer):
        """
        if friend request accepted, both users are added as friends.
        if unaccepted, friendship is removed if it previously existed
        """
        friendship_request = serializer.save()

        if friendship_request:
            requester = friendship_request.requested_by
            receiver = friendship_request.requested_to

            if friendship_request.accepted:
                # Add to each other's friends lists only if not already added
                if receiver not in requester.friends.all():
                    requester.friends.add(receiver)

                # add friend entry to both vector stores
                page_content = f"{requester.email} is my friend"
                metadata = {"type": "friend", "id": str(requester.id)}
                update_vector_store_for_user.delay(
                    receiver.id,
                    page_content=page_content,
                    metadata=metadata,
                    action="create",
                )
                page_content = f"{receiver.email} is my friend"
                metadata = {"type": "friend", "id": str(receiver.id)}
                update_vector_store_for_user.delay(
                    requester.id,
                    page_content=page_content,
                    metadata=metadata,
                    action="create",
                )
                # delete request entry from both vector stores
                metadata = {
                    "type": "received friend request",
                    "id": str(friendship_request.id),
                }
                update_vector_store_for_user.delay(
                    receiver.id, metadata=metadata, action="delete"
                )
                metadata = {
                    "type": "sent friend request",
                    "id": str(friendship_request.id),
                }
                update_vector_store_for_user.delay(
                    requester.id, metadata=metadata, action="delete"
                )

            else:
                # Remove from each other's friends lists if the request is unaccepted
                if receiver in requester.friends.all():
                    requester.friends.remove(receiver)

                # delete friend entry from both vector stores
                metadata = {"type": "friend", "id": str(receiver.id)}
                update_vector_store_for_user.delay(
                    requester.id, metadata=metadata, action="delete"
                )
                metadata = {"type": "friend", "id": str(requester.id)}
                update_vector_store_for_user.delay(
                    receiver.id, metadata=metadata, action="delete"
                )

    def perform_destroy(self, instance):
        """remove friendship if exists, when request is deleted"""
        requester = instance.requested_by
        receiver = instance.requested_to

        if instance.accepted:
            requester.friends.remove(receiver)

            # delete friend entry from both vector stores
            metadata = {"type": "friend", "id": str(requester.id)}
            update_vector_store_for_user.delay(
                receiver.id, metadata=metadata, action="delete"
            )
            metadata = {"type": "friend", "id": str(receiver.id)}
            update_vector_store_for_user.delay(
                requester.id, metadata=metadata, action="delete"
            )

        else:
            # delete request entry from both vector stores
            metadata = {"type": "received friend request", "id": str(instance.id)}
            update_vector_store_for_user.delay(
                receiver.id, metadata=metadata, action="delete"
            )
            metadata = {"type": "sent friend request", "id": str(instance.id)}
            update_vector_store_for_user.delay(
                requester.id, metadata=metadata, action="delete"
            )

        instance.delete()


class RequestsSentView(generics.ListAPIView):
    """sent request list"""

    serializer_class = FriendRequestSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsRequesterOrReceiverOrCreateOnly,
    ]

    def get_queryset(self):
        """restrict queryset to friend requests from currently authenticated user"""
        sent = (
            FriendRequest.objects.all()
            .filter(requested_by=self.request.user)
            .filter(accepted=False)
        )
        return sent


class RequestsReceivedView(generics.ListAPIView):
    """received requests list"""

    serializer_class = FriendRequestSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsRequesterOrReceiverOrCreateOnly,
    ]

    def get_queryset(self):
        """restrict queryset to friend requests to currently authenticated user"""
        received = (
            FriendRequest.objects.all()
            .filter(requested_to=self.request.user)
            .filter(accepted=False)
        )
        return received
