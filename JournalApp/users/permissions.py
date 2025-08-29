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
