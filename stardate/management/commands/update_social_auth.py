import logging

from django.core.management.base import BaseCommand

from social.apps.django_app.default.models import UserSocialAuth

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Updates the extra_data key on a UserSocialAuth object created with
    django-social-auth to a compatible UserSocialAuth object for
    python-social-auth.
    """

    def handle(self, *args, **options):
        for social_auth in UserSocialAuth.objects.all():
            self.convert_social_auth(social_auth)

    def convert_social_auth(self, auth_obj):
        access_token = auth_obj.extra_data['access_token']

        auth_obj.extra_data['access_token'] = {
            'oauth_token_secret': access_token.split('&')[0].split('=')[1],
            'oauth_token': access_token.split('&')[1].split('=')[1],
            'uid': auth_obj.uid,
        }
        auth_obj.extra_data['expires'] = 'null'
        auth_obj.extra_data['id'] = 'null'

        auth_obj.save()
