""" friends models """

from django.db import models


class FriendRequest(models.Model):
    """Friend Request can be sent/received to/from a user, and can be accepted/deleted"""

    created_at = models.DateField(auto_now_add=True)
    requested_by = models.ForeignKey(
        "users.CustomUser", related_name="requests_sent", on_delete=models.CASCADE
    )
    requested_to = models.ForeignKey(
        "users.CustomUser", related_name="requests_received", on_delete=models.CASCADE
    )
    accepted = models.BooleanField(default=False)
