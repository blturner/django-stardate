from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from stardate.models import Blog


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
                    for blog in Blog.objects.filter(owner=user.id):
                        blog.save_post_objects()
                except User.DoesNotExist:
                    print u'User with username %s does not exist.' % username
        else:
            for user in User.objects.all():
                try:
                    for blog in Blog.objects.filter(owner=user.id):
                        blog.save_post_objects()
                except:
                    pass
