import json

from django.test import TestCase
from social_auth.models import UserSocialAuth

from stardate.models import DropboxFile
from stardate.sync import StardateSync


class MockDropboxClient(object):
    entry_data = [['/test_file.md', {
        'size': '452 bytes',
        'rev': '7cb07486f6b',
        'thumb_exists': False,
        'bytes': 452,
        'modified': 'Mon, 16 Jul 2012 00:32:36 +0000',
        'mime_type': 'application/octet-stream',
        'path': '/test_file.md',
        'is_dir': False,
        'icon': 'page_white',
        'root': 'app_folder',
        'client_mtime': 'Mon, 16 Jul 2012 00:32:36 +0000',
        'revision': 1995}]]

    data = json.dumps({
        'entries': entry_data,
        'reset': False,
        'cursor': None,
        'has_more': False
    })

    def __init__(self, sess=None):
        self.sess = sess

    def delta(self, cursor):
        return json.loads(self.data)

    def get_file(self, path):
        f = MockFile()
        return f

    def put_file(self, full_path, file_obj, overwrite=False, parent_rev=None):
        return True


class MockFile(object):
    def read(self):
        return 'title: Hello world\npublish: 2012-06-01 6:00 AM\n\n\nThe post content.'


class StardateSyncTestCase(TestCase):
    fixtures = ['dump.json']

    def setUp(self):
        super(StardateSyncTestCase, self).setUp()

        self.auth = UserSocialAuth.objects.get(pk=2)
        self.sync = StardateSync(self.auth, client=MockDropboxClient)

    def test_stardatesync_has_auth(self):
        self.assertTrue(self.sync.auth)
        self.assertEqual(self.sync.auth.provider, 'dropbox')

    def test_get_access_token(self):
        access_token = self.sync.get_access_token()

        self.assertEqual(access_token['oauth_token'], 'jpjn7wsyilznvw2')
        self.assertEqual(access_token['oauth_token_secret'], 'bqdb1ohoja9iiwf')

    def test_get_cursor(self):
        self.assertEqual(self.sync.cursor, u'AuZOCpmuHVM9SxPssXqA0dve0nC2A64zsxqxWPkzJ0JGeJxjYKzqZGD4P5HdIz-bgYEzlAEIADSHBBw')
        self.sync.auth.extra_data['cursor'] = None
        self.assertRaises('KeyError', self.sync.get_cursor())

    def test_save_cursor(self):
        self.sync.save_cursor('test_string')
        self.assertEqual(self.sync.get_cursor(), 'test_string')
        self.assertEqual(self.sync.cursor, 'test_string')

    def test_get_dropbox_client(self):
        self.assertIsInstance(self.sync.dropbox_client, MockDropboxClient)

    def test_process_dropbox_entries(self):
        self.sync.process_dropbox_entries()
        df = DropboxFile.objects.get(path='/test_file.md')

        self.assertEqual(DropboxFile.objects.count(), 1)
        self.assertEqual(df.path, u'/test_file.md')
        self.assertEqual(df.size, u'452 bytes')
        self.assertEqual(df.content, u'title: Hello world\npublish: 2012-06-01 6:00 AM\n\n\nThe post content.')
