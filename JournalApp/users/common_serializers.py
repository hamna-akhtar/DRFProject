from rest_framework import serializers
from .models import CustomUser

# to avoid recursion in nested data display
class UserMiniSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ("id", "email", "username")
