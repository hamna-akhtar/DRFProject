"""
Signal to clear chat history on logout
"""
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from .models import ChatMessage


@receiver(user_logged_out)
def clear_chat_on_logout(sender, request, user, **kwargs):
    """clear chat history when user logs out"""
    if user:
        deleted_count, _ = ChatMessage.objects.filter(user=user).delete()
        print(f"cleared {deleted_count} chat messages for user {user.id} on logout")