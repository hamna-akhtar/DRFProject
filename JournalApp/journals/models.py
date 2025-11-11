""" journals models """

from django.db import models


class JournalEntry(models.Model):
    """
    journal entry is created by a user.
    may be private, public, or shared with other users.
    action items are extracted from its content to create related tasks
    """

    created_at = models.DateField(auto_now_add=True)
    author = models.ForeignKey(
        "users.CustomUser", related_name="journal_entries", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=100, blank=True, default="")
    content = models.TextField()
    access = models.CharField(
        choices=[("private", "Private"), ("public", "Public"), ("custom", "Custom")],
        default="private",
    )
    shared_to = models.ManyToManyField("users.CustomUser")


class Task(models.Model):
    """action item extracted from a user's journal entry"""

    created_at = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(
        "users.CustomUser", related_name="tasks", on_delete=models.CASCADE
    )
    description = models.TextField()
    from_journal = models.ForeignKey(
        "journals.JournalEntry",
        related_name="tasks",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
