"""celery task to generate AI response"""

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import traceback
from .chatbot import create_chatbot
from .models import ChatMessage

chatbot = None


@shared_task
def generate_response_task(user_id, message, room_name):
    """Generate AI response"""
    global chatbot
    try:
        if chatbot is None:
            chatbot = create_chatbot(user_id)
        response = chatbot.chat(message)

        # send bot response through websocket
        ChatMessage.objects.create(
            user_id=user_id, role='bot', content=response
        )
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_name, {"type": "chat_response", "message": response}
        )

    except Exception as e:
        print(f"Error generating response: {e}")
        traceback.print_exc()

        ChatMessage.objects.create(
            user_id=user_id, role='bot', content=f"an error occurred: {str(e)}"
        )
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_name,
            {"type": "chat_response", "message": f"an error occurred: {str(e)}"},
        )
