"""chat models"""
from django.db import models
from django.conf import settings


class ChatMessage(models.Model):
    """Store all chat messages for conversation history"""
    user = models.ForeignKey("users.CustomUser", related_name="chat_messages", on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('bot', 'Bot')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']