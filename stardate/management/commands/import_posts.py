import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.transaction import atomic

from optparse import make_option

from stardate.models import Blog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Usage:
    ./manage.py import_posts --user [username] --user [otheruser]

    When importing posts from the backend, a backend should check that
    there is new data on the backend itself, if there is new data, then
    the backend may fetch new data to be updated.

    """
    option_list = BaseCommand.option_list + (
        make_option(
            '--user',
            action='append',
            dest='user',
            default=[],
            help='Specify a username to fetch blog posts'
        ),
    )

    def handle(self, *args, **options):
        if options['user']:
            users = User.objects.filter(username__in=options['user'])
        else:
            users = User.objects.all()

        for user in users:
            for blog in Blog.objects.filter(user=user):
                logger.info(u'Updating posts for {0}'.format(blog))

                posts = blog.backend.pull(blog)
                self.batch_save(posts)

    @atomic
    def batch_save(self, queryset):
        for obj in queryset:
            push = False

            if obj.stardate:
                push = True

            obj.save(push=push)