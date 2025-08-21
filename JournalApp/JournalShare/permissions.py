from rest_framework import permissions


class IsSelfOrReadOnly(permissions.BasePermission):
    """
    anyone can view list/detail users
    only logged-in user can update/delete own profile.
    """
    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            return True

        return obj == request.user


class JournalPermission(permissions.BasePermission):
    """
    for private -> only author can read/write.
    for public -> everyone can read, only author can write.
    for custom -> author and shared_to users can read, only author can write.
    """

    def has_object_permission(self, request, view, obj):
        if obj.author == request.user:
            return True

        if request.method == 'GET':
            if obj.access == "public":
                return True
            elif obj.access == "custom":
                return request.user in obj.shared_to.all()
            elif obj.access == "private":
                return False
            else:
                return False
        return False


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
