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

        if request.method == "DELETE" or request.method == "GET":
            return obj.requested_by == request.user or obj.requested_to == request.user

        if  request.method == "PUT" or request.method == "PATCH":
            return obj.requested_to == request.user

        return False
