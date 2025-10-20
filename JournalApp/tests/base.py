""" helper class for tests of all apps """

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate
from django.test import TestCase
from users.models import CustomUser


class CustomBaseTestCase(TestCase):
    """base test class providing common users and request factory setup"""

    def setUp(self):
        """set up test users and API factory."""
        self.factory = APIRequestFactory()
        self.user1 = CustomUser.objects.create(
            email="user1@gmail.com",
            first_name="ben",
            last_name="adams",
            password="abcdef",
        )
        self.user2 = CustomUser.objects.create(
            email="user2@gmail.com", password="ghijkl"
        )
        self.user3 = CustomUser.objects.create(
            email="user3@gmail.com", password="mnopqr"
        )

    def create_request_context(self, user):
        """helper to create request context with authentication for serializer"""
        request = self.factory.get("/")
        force_authenticate(request, user=user)
        request.user = user
        return {"request": Request(request)}
