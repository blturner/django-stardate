import datetime

from django.test import TestCase
from django.utils import timezone

from stardate.backends.dropbox import DropboxBackend
from stardate.tests.mock_dropbox import MockDropboxClient


class DropboxBackendTestCase(TestCase):
    def setUp(self):
        self.backend = DropboxBackend()
        self.backend.client = MockDropboxClient()

    def test_get_name(self):
        self.assertEqual(self.backend.get_name(), 'dropbox')

    def test_get_file_list(self):
        file_list = self.backend.get_file_list()

        self.assertEqual(file_list, [(0, u'/test_file.md')])
        self.assertEqual(len(file_list), 1)

    def test_sync(self):
        post_list = [{
            'fields': {'body': u'Do it.\n',
                    'publish': datetime.datetime(2013, 1, 4, 8, 0, tzinfo=timezone.utc),
                    'stardate': u'352b967d-87bf-11e2-81f3-b88d120c8298',
                    'title': u'Fourth post'},
            'model': u'stardate.post',
            'pk': 27, }]
        sync = self.backend.sync('/test_path', post_list)

        self.assertEqual(sync.read(), 'stardate: 352b967d-87bf-11e2-81f3-b88d120c8298\npublish: 2013-01-04 12:00 AM\ntitle: Fourth post\n\n\nDo it.\n')
