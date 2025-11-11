"""websocket handler"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import posthog
from .tasks import generate_response_task
from .models import ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):
    """connect to frontend, send chatbot responses, and receive user messages"""

    # track active connections per user
    active_channels = {}

    async def connect(self):
        """websocket connect"""
        self.user = self.scope["user"]
        self.user_email = self.user.email
        if self.user.is_anonymous:
            await self.close()
            return

        self.user_id = self.user.id
        self.group_name = f"chat_{self.user_id}"

        # close any existing connection for this user
        if self.user_id in self.active_channels:
            old_channel = self.active_channels[self.user_id]
            print(f"Closing duplicate connection for user {self.user_id}")
            try:
                await self.channel_layer.group_discard(self.group_name, old_channel)
            except:
                pass

        # register this connection
        self.active_channels[self.user_id] = self.channel_name
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # load chat history and send to frontend
        history = await self.load_chat_history()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "history",
                    "messages": history,
                }
            )
        )

        # await self.send(json.dumps({
        #     'type': 'system',
        #     'message': 'Connected!'
        # }))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        # remove from active channels
        if hasattr(self, "user_id"):
            if self.active_channels.get(self.user_id) == self.channel_name:
                del self.active_channels[self.user_id]
                print(f"removed user {self.user_id} from active connections")

    async def receive(self, text_data):
        """user sent a message"""
        data = json.loads(text_data)
        message_type = data.get("type", "message")

        if message_type == "clear_history":
            deleted_count = await self.delete_all_messages()
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "history_cleared",
                        "message": f"Chat history cleared ({deleted_count} messages deleted)",
                    }
                )
            )
            return

        user_message = data.get("message", "").strip()
        if not user_message:
            return

        # posthog.capture(
        #     distinct_id=self.user_email,
        #     event='user sent msg',
        #     properties={
        #         "user_id": self.user_id,
        #         "user_email": self.user_email,
        #         "channel_name": self.channel_name,
        #         "group_name": self.group_name,
        #         "user_message": user_message
        #     }
        # )

        await self.save_message_to_db("user", user_message)
        await self.send(json.dumps({"type": "typing", "is_typing": True}))

        generate_response_task.delay(self.user_id, user_message, self.group_name)

    async def chat_response(self, event):
        """celery sent a response"""

        # only send to the active connection for this user
        if self.active_channels.get(self.user_id) == self.channel_name:
            # await self.save_message_to_db("bot", event["message"])
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "bot",
                        "message": event["message"],
                    }
                )
            )
        else:
            print(f"skipping message to inactive connection for user {self.user_id}")

    @database_sync_to_async
    def load_chat_history(self):
        """load all chat messages for this user"""
        messages = ChatMessage.objects.filter(user_id=self.user_id).order_by(
            "created_at"
        )

        return [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

    @database_sync_to_async
    def save_message_to_db(self, role, content):
        """save message to db for chat history"""
        return ChatMessage.objects.create(
            user_id=self.user_id, role=role, content=content
        )

    @database_sync_to_async
    def delete_all_messages(self):
        """delete all messages for this user"""
        count, _ = ChatMessage.objects.filter(user_id=self.user_id).delete()
        return count
