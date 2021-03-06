import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

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
    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', dest='force')

        parser.add_argument(
            '--user',
            action='append',
            dest='user',
            default=[],
            help='Specify a username to fetch blog posts'
        )

    def handle(self, *args, **options):
        force = options['force'] or False

        if options['user']:
            users = User.objects.filter(username__in=options['user'])
        else:
            users = User.objects.all()

        for user in users:
            for blog in Blog.objects.filter(user=user):
                logger.info(u'Updating posts for {0}'.format(blog))

                blog.backend.pull(force=force)
