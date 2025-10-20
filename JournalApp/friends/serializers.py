"""
friends serializers
handle friend request create, list and
accepting friend requests between users
"""

from rest_framework import serializers
from users.models import CustomUser
from users.common_serializers import UserMiniSerializer
from .models import FriendRequest


class FriendRequestSerializer(serializers.ModelSerializer):
    """serializer for FriendRequest model"""

    request_from = UserMiniSerializer(source="requested_by", read_only=True)
    request_to = UserMiniSerializer(source="requested_to", read_only=True)

    send_request_to = serializers.PrimaryKeyRelatedField(
        source="requested_to", queryset=CustomUser.objects.none(), write_only=True
    )

    class Meta:
        model = FriendRequest
        fields = [
            "id",
            "created_at",
            "request_from",
            "request_to",
            "send_request_to",
            "accepted",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "request_from",
            "request_to",
            "accepted",
        ]

    def get_fields(self):
        """
        hide curr user and users already in requests to/from me,
        from the 'request to' menu when sending friend request
        """
        fields = super().get_fields()
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            user = request.user
            fields["send_request_to"].queryset = (
                CustomUser.objects.exclude(id=user.id)
                .exclude(
                    id__in=FriendRequest.objects.filter(requested_by=user).values_list(
                        "requested_to_id", flat=True
                    )
                )
                .exclude(
                    id__in=FriendRequest.objects.filter(requested_to=user).values_list(
                        "requested_by_id", flat=True
                    )
                )
            )
        return fields


class FriendAcceptSerializer(serializers.ModelSerializer):
    """serializer for the accepted field from FriendRequest model"""

    class Meta:
        model = FriendRequest
        fields = ["accepted"]
