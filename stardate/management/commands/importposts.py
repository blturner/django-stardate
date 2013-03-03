from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from stardate.sync import StardateSync


class Command(BaseCommand):
    """
    Usage:
    ./manage.py import_posts [username ...]
    """
    args = '<username username ...>'
    help = 'Imports posts for the specified blogs'

    def handle(self, *args, **kwargs):
        if args:
            for username in args:
                try:
                    user = User.objects.get(username=username)
                    print user
                except User.DoesNotExist:
                    print u'User with username %s does not exist.' % username
        else:
            for user in User.objects.all():
                try:
                    dropbox_auth = user.social_auth.get(provider='dropbox')
                    sync = StardateSync(dropbox_auth)
                    sync.process_dropbox_entries()
                except:
                    pass
