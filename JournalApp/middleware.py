import datetime
from datetime import datetime
import environ
import jwt
import pytz
import requests
from jwt.algorithms import RSAAlgorithm
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from users.models import CustomUser as User

env = environ.Env()

CLERK_API_URL = "https://api.clerk.com/v1"
CLERK_FRONTEND_API_URL = env("CLERK_FRONTEND_API_URL")
CLERK_SECRET_KEY = env("CLERK_SECRET_KEY")
CACHE_KEY = "jwks_data"


class JWTAuthenticationMiddleware(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # print("no auth header")
            return None
        try:
            token = auth_header.split(" ")[1]
        except IndexError as exc:
            raise AuthenticationFailed("Bearer token not provided.") from exc
        user = self.decode_jwt(token)

        clerk = ClerkSDK()
        info, found = clerk.fetch_user_info(user.clerk_id)
        if not user:
            return None
        if found:
            user.email = info.get("email_address") or ""
            user.first_name = info.get("first_name") or ""
            user.last_name = info.get("last_name") or ""
            user.last_login = info.get("last_login") or ""
        user.save()
        return user, None

    def decode_jwt(self, token):
        clerk = ClerkSDK()
        jwks_data = clerk.get_jwks()
        # jwk = jwks_data["keys"][0]
        # public_key = jwt.PyJWK(jwk).key()
        public_key = RSAAlgorithm.from_jwk(jwks_data["keys"][0])
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_signature": True},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationFailed("Token has expired.") from exc
        except jwt.DecodeError as exc:
            raise AuthenticationFailed("Token decode error.") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed("Invalid token.") from exc

        # payload contains sub(user id in clerk), email, exp(expiry date)
        user_id = payload.get(
            "sub"
        )  # user_id in clerk used to get/create django user of this clerk_id
        if user_id:
            user, _ = User.objects.get_or_create(clerk_id=user_id)
            return user
        return None


class ClerkSDK:
    def fetch_user_info(self, user_id: str):
        response = requests.get(
            f"{CLERK_API_URL}/users/{user_id}",
            headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "email_address": data["email_addresses"][0]["email_address"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "last_login": datetime.fromtimestamp(
                    data["last_sign_in_at"] / 1000, tz=pytz.UTC
                ),
            }, True

        return {
            "email_address": "",
            "first_name": "",
            "last_name": "",
            "last_login": None,
        }, False

    def get_jwks(self):
        jwks_data = cache.get(CACHE_KEY)
        if not jwks_data:
            response = requests.get(
                f"{CLERK_FRONTEND_API_URL}/.well-known/jwks.json", timeout=10
            )
            if response.status_code == 200:
                jwks_data = response.json()
                cache.set(CACHE_KEY, jwks_data)
            else:
                raise AuthenticationFailed("Failed to fetch JWKS.")
        return jwks_data
