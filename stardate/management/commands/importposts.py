from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = '<blog_id blog_id ...>'
    help = 'Imports posts for the specified blogs'

    def handle(self, *args, **kwargs):
        for blog_id in args:
            print blog_id
