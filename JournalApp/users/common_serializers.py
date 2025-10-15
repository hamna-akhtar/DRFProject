""" common serializers for all apps of this project """

from rest_framework import serializers
from .models import CustomUser


class UserMiniSerializer(serializers.ModelSerializer):
    """to avoid recursion in nested data display of user"""

    class Meta:
        model = CustomUser
        fields = ("id", "email", "first_name", "last_name")
