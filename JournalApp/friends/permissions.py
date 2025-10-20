""" friends permissions """

from rest_framework import permissions


class IsRequesterOrReceiverOrCreateOnly(permissions.BasePermission):
    """
    anyone can create friend request
    only requestor or receiver can view/list/delete
    only receiver can accept(update) request
    """

    def has_object_permission(self, request, view, obj):
        if request.method == "POST":
            return True

        if request.method in ("DELETE", "GET"):
            return request.user in (obj.requested_by, obj.requested_to)

        if request.method in ("PUT", "PATCH"):
            return obj.requested_to == request.user

        return False
