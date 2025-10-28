"""celery task to generate AI response"""

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import traceback
from .chatbot import create_chatbot

chatbot = None


@shared_task
def generate_response_task(user_id, message, room_name):
    """Generate AI response"""
    global chatbot
    try:
        # Create chatbot
        if chatbot is None:
            chatbot = create_chatbot(user_id)
        # Generate response
        response = chatbot.chat(message)

        # Send via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_name, {"type": "chat_response", "message": response}
        )

    except Exception as e:
        print(f"Error generating response: {e}")
        traceback.print_exc()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_name,
            {"type": "chat_response", "message": f"Sorry, an error occurred: {str(e)}"},
        )
