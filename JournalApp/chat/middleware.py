"""clerk authentication middleware for WebSockets"""

from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs
import jwt
from jwt.algorithms import RSAAlgorithm
from middleware import ClerkSDK
from users.models import CustomUser as User


class ClerkAuthMiddleware(BaseMiddleware):
    """authenticate WebSocket connections using clerk token"""

    async def __call__(self, scope, receive, send):
        # extract token from query string
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            scope["user"] = await self.get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        """verify clerk token and return user"""
        try:
            clerk = ClerkSDK()
            jwks_data = clerk.get_jwks()
            public_key = RSAAlgorithm.from_jwk(jwks_data["keys"][0])

            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_signature": True},
            )

            clerk_id = payload.get("sub")
            if not clerk_id:
                return AnonymousUser()

            user, _ = User.objects.get_or_create(clerk_id=clerk_id)
            return user

        except (jwt.ExpiredSignatureError, jwt.DecodeError, jwt.InvalidTokenError) as e:
            print(f"Token verification failed: {e}")
            return AnonymousUser()
        except Exception as e:
            print(f"Authentication error: {e}")
            return AnonymousUser()
