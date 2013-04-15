import datetime

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from social_auth.models import UserSocialAuth

from stardate.backends.dropbox import DropboxBackend
from stardate.tests.factories import create_user, create_user_social_auth
from stardate.tests.mock_dropbox import MockDropboxClient


class DropboxBackendTestCase(TestCase):
    def setUp(self):
        self.backend = DropboxBackend()
        self.backend.client = MockDropboxClient()
        self.backend.client_class = MockDropboxClient

        social_auth = create_user_social_auth(user=create_user())
        self.backend.set_social_auth(social_auth)

    def test_get_access_token(self):
        access_token = self.backend.get_access_token()

        self.assertEqual(access_token['oauth_token_secret'], 'oauth_token_secret_string')
        self.assertEqual(access_token['oauth_token'], 'oauth_token_string')

    def test_cursor(self):
        self.assertEqual(self.backend.get_cursor(), None)
        self.backend.save_cursor('testing_cursor')
        self.assertEqual(self.backend.get_cursor(), 'testing_cursor')

    def test_get_dropbox_client(self):
        self.assertIsInstance(self.backend.get_dropbox_client(), MockDropboxClient)

    def test_get_name(self):
        self.assertEqual(self.backend.get_name(), 'dropbox')

    def test_delta(self):
        self.assertEqual(self.backend.get_cursor(), None)
        delta = self.backend.delta()
        self.assertEqual(self.backend.get_cursor(), 'VAU6GZG5NK31AW2YD8H7UDWE0W74VV')
        self.assertTrue(delta.get('entries'))
        self.assertEqual(delta.get('entries')[0][0], '/test_file.md')

    def test_get_file(self):
        backend_file = self.backend.get_file('/test_file.md')
        self.assertEqual(backend_file, "publish: 2012-01-02 12:00 AM\ntitle: Tingling of the spine\n\n\nExtraordinary claims require extraordinary evidence!\n\n---\n\npublish: 2012-01-01 06:00 AM\ntitle: Great turbulent clouds\n\n\nWith pretty stories for which there's little good evidence.\n")

    def test_get_posts(self):
        post_list = self.backend.get_posts('/test_file.md')
        self.assertEqual(len(post_list), 2)
        self.assertEqual(post_list[0]['title'], 'Tingling of the spine')
        self.assertEqual(post_list[1]['title'], 'Great turbulent clouds')

    def test_get_source_list(self):
        source_list = self.backend.get_source_list()
        self.assertEqual(len(source_list), 4)

    def test_has_update(self):
        self.assertFalse(self.backend.has_update())

    def test_save_cursor(self):
        self.backend.save_cursor('test_cursor')
        self.assertEqual(self.backend.cursor, 'test_cursor')

    def test_set_social_auth(self):
        user = User.objects.get(username='bturner')
        social_auth = UserSocialAuth.objects.get(user__exact=user.id)

        self.backend.social_auth = None
        self.assertEqual(self.backend.social_auth, None)

        self.backend.set_social_auth(social_auth)
        self.assertIsInstance(self.backend.social_auth, UserSocialAuth)

    def test_sync(self):
        post_list = [{
            'fields': {
                'body': u'Do it.\n',
                'publish': datetime.datetime(2013, 1, 4, 8, 0, tzinfo=timezone.utc),
                'stardate': u'352b967d-87bf-11e2-81f3-b88d120c8298',
                'title': u'Fourth post'},
            'model': u'stardate.post', 'pk': 27, }]

        sync = self.backend.sync('/test_path', post_list)

        self.assertEqual(sync.read(), 'stardate: 352b967d-87bf-11e2-81f3-b88d120c8298\npublish: 2013-01-04 12:00 AM\ntitle: Fourth post\n\n\nDo it.\n')
