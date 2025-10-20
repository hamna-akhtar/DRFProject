""" journals permissions"""

from rest_framework import permissions


class JournalPermission(permissions.BasePermission):
    """
    for private -> only author can read/write.
    for public -> everyone can read, only author can write.
    for custom -> author and shared_to users can read, only author can write.
    """

    def has_object_permission(self, request, view, obj):
        if obj.author == request.user:
            return True

        if request.method == "GET":
            if obj.access == "public":
                return True
            if obj.access == "custom":
                return request.user in obj.shared_to.all()
            if obj.access == "private":
                return False
        return False
