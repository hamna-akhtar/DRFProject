from django.db import models


class JournalEntry(models.Model):
    created_at = models.DateField(auto_now_add=True)
    author = models.ForeignKey('users.CustomUser', related_name='journal_entries', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True, default='')
    content = models.TextField()
    access = models.CharField(
        choices=[('private', 'Private'), ('public', 'Public'), ('custom', 'Custom')],
        default='private')
    shared_to = models.ManyToManyField('users.CustomUser')
