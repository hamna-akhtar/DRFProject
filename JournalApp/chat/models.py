"""chat models"""

from django.db import models


class ChatMessage(models.Model):
    """store all chat messages"""

    user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10, choices=[("user", "User"), ("bot", "Bot"), ("system", "System")]
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
