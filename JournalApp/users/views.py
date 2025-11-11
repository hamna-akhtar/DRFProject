"""users views"""

from rest_framework import generics
from rest_framework import permissions
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from svix.webhooks import Webhook, WebhookVerificationError
import environ
from friends.models import FriendRequest
from chat.tasks import update_vector_store_for_user, delete_vector_store_for_user
from .models import CustomUser
from .serializers import UserSerializer
from .permissions import IsSelfOrReadOnly


class UserListView(generics.ListAPIView):
    """list of users"""

    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class MyProfileView(generics.RetrieveAPIView):
    """user detail for currently authenticated user"""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserDetailView(generics.RetrieveUpdateAPIView):
    """user detail and update"""

    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelfOrReadOnly]
    lookup_field = "pk"


class DiscoverFriendsView(generics.ListAPIView):
    """list of users that are neither friend of, nor are there any friend requests
    to/from them to currently authenticated user"""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return (
            CustomUser.objects.exclude(id=user.id)
            .exclude(
                id__in=FriendRequest.objects.filter(requested_by=user).values_list(
                    "requested_to_id", flat=True
                )
            )
            .exclude(
                id__in=FriendRequest.objects.filter(requested_to=user).values_list(
                    "requested_by_id", flat=True
                )
            )
        )


env = environ.Env()
CLERK_WEBHOOK_SIGNING_SECRET = env("CLERK_WEBHOOK_SIGNING_SECRET")


@csrf_exempt
def clerk_webhook(request):
    """listens to clerk webhooks to sync db user data with clerk user data"""
    # print("webhook received")

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    svix_id = request.headers.get("svix-id")
    svix_timestamp = request.headers.get("svix-timestamp")
    svix_signature = request.headers.get("svix-signature")

    if not svix_id or not svix_timestamp or not svix_signature:
        return JsonResponse({"error": "Missing svix headers"}, status=400)

    # verify the webhook using svix
    wh = Webhook(CLERK_WEBHOOK_SIGNING_SECRET)

    try:
        payload = wh.verify(
            request.body,
            {
                "svix-id": svix_id,
                "svix-timestamp": svix_timestamp,
                "svix-signature": svix_signature,
            },
        )
    except WebhookVerificationError as e:
        print(f"Webhook verification failed: {e}")
        return JsonResponse({"error": "Invalid signature"}, status=400)

    try:
        event_type = payload.get("type")
        data = payload.get("data", {})

        clerk_id = data.get("id")
        email = (
            data.get("email_addresses", [{}])[0].get("email_address")
            if data.get("email_addresses")
            else None
        )
        first_name = data.get("first_name")
        last_name = data.get("last_name")

        # print(event_type, clerk_id)
        # print(email, first_name, last_name)

        if event_type == "user.updated":
            print("Processing user update...")
            user, _ = CustomUser.objects.update_or_create(
                clerk_id=clerk_id,
                defaults={
                    "email": email,
                    "first_name": first_name or "",
                    "last_name": last_name or "",
                },
            )

            page_content = f"My Profile: {user}"
            metadata = {"type": "my profile", "id": str(user.id)}
            update_vector_store_for_user.delay(
                user.id, page_content=page_content, metadata=metadata, action="update"
            )

        elif event_type == "user.created":
            print("Processing user creation...")
            CustomUser.objects.get_or_create(
                clerk_id=clerk_id,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )

        elif event_type == "user.deleted":
            print("Processing user deletion...")
            user = CustomUser.objects.get(clerk_id=clerk_id)
            if user:
                delete_vector_store_for_user(user.id)
                user.delete()

        return JsonResponse({"status": "success", "event": event_type}, status=200)

    except Exception as e:
        print(f"Webhook processing error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
