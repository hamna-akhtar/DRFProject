from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    clerk_id = models.CharField(unique=True, null=True)
    email = models.EmailField(unique=True)
    friends = models.ManyToManyField('self', blank=True)

    username = models.CharField(max_length=150, blank=True, null=True, unique=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
