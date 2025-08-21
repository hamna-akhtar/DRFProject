from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    friends = models.ManyToManyField('self', blank=True)

class JournalEntry(models.Model):
    created_at = models.DateField(auto_now_add=True)
    author = models.ForeignKey('CustomUser', related_name='journal_entries', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True, default='')
    content = models.TextField()
    access = models.CharField(
        choices=[('private', 'Private'), ('public', 'Public'), ('custom', 'Custom')],
        default='private')
    shared_to = models.ManyToManyField('CustomUser')

class FriendRequest(models.Model):
    created_at = models.DateField(auto_now_add=True)
    requested_by = models.ForeignKey('CustomUser', related_name='requests_sent', on_delete=models.CASCADE)
    requested_to = models.ForeignKey('CustomUser', related_name='requests_received', on_delete=models.CASCADE)
    accepted = models.BooleanField(default=False)
