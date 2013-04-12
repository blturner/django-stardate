from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from stardate.models import Blog


class Command(BaseCommand):
    """
    Usage:
    ./manage.py import_posts [username ...]

    When importing posts from the backend, a backend should check that
    there is new data on the backend itself, if there is new data, then
    the backend may fetch new data to be updated.

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
                        print 'Processing %s, %s' % (blog.name, blog.get_backend_choice())
                        post_list = blog.backend.do_sync(blog.get_backend_choice())
                        if post_list:
                            blog.save_post_objects(post_list)
                except:
                    raise
