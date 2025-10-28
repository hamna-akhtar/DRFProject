"""websocket handler"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from .models import ChatMessage
from .tasks import generate_response_task


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
            return

        self.user_id = self.user.id
        self.room_name = f"chat_{self.user_id}"

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        await self.send(json.dumps({
            'type': 'system',
            'message': 'Connected! Ask me anything about your journals, tasks and friends.'
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        """user sent a message"""
        data = json.loads(text_data)
        user_message = data.get('message', '').strip()

        if not user_message:
            return

        await self.save_message('user', user_message)

        await self.send(json.dumps({'type': 'typing', 'is_typing': True}))

        # generate response in background with celery task
        generate_response_task.delay(self.user_id, user_message, self.room_name)

    async def chat_response(self, event):
        """celery sent a response"""
        await self.send(json.dumps({
            'type': 'bot',
            'message': event['message']
        }))

    @database_sync_to_async
    def save_message(self, role, content):
        ChatMessage.objects.create(user_id=self.user_id, role=role, content=content)