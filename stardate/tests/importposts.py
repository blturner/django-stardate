import json

from django.core import management
from django.test import TestCase
from dropbox import client
from mock import Mock, patch

from stardate.dropbox_auth import DropboxAuth
from stardate.models import Blog, DropboxFile, Post
# from stardate.parser import ParseError


class ImportTestCase(TestCase):
    fixtures = ['stardate_parser_testdata.json']

    def setUp(self):
        super(ImportTestCase, self).setUp()

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

        mock_file = Mock(spec=file)
        mock_file.read.return_value = 'title: Hello world\npublish: 2012-06-01 6:00 AM\n\n\nThe post content.'

        mock_dropbox_client = Mock()
        mock_dropbox_client.delta.return_value = json.loads(data)
        mock_dropbox_client.get_file.return_value = mock_file

        self.MockDropboxAuth = Mock(spec=DropboxAuth)
        self.MockDropboxAuth.dropbox_client = mock_dropbox_client

        invalid_mock_file = Mock(spec=file)
        invalid_mock_file.read.return_value = 'invalid test string.'

        invalid_mock_dropbox_client = Mock()
        invalid_mock_dropbox_client.delta.return_value = json.loads(data)
        invalid_mock_dropbox_client.get_file.return_value = invalid_mock_file

        self.InvalidMockDropboxAuth = Mock(spec=DropboxAuth)
        self.InvalidMockDropboxAuth.dropbox_client = invalid_mock_dropbox_client

    def test_importposts(self):
        management.call_command('importposts', client=self.MockDropboxAuth)

        imported_file = DropboxFile.objects.get(path='/test_file.md')
        self.assertTrue(imported_file)
        self.assertEqual(imported_file.content, 'title: Hello world\npublish: 2012-06-01 6:00 AM\n\n\nThe post content.')

    @patch.object(client.DropboxClient, 'put_file')
    def test_importposts_created_post(self, mock_put_file):
        management.call_command('importposts', client=self.MockDropboxAuth)
        blog = Blog(name='Test blog', slug='test-blog',
            dropbox_file=DropboxFile.objects.get(path='/test_file.md'))
        blog.save()
        management.call_command('importposts', client=self.MockDropboxAuth)

        self.assertEqual(Post.objects.get(title='Hello world').title, 'Hello world')

    @patch.object(client.DropboxClient, 'put_file')
    def test_import_invalid_posts(self, mock_put_file):
        management.call_command('importposts', client=self.InvalidMockDropboxAuth)
        blog = Blog(name='Test blog', slug='test-blog',
            dropbox_file=DropboxFile.objects.get(path='/test_file.md'))
        blog.save()
        management.call_command('importposts', client=self.InvalidMockDropboxAuth)

        self.assertEqual(Post.objects.count(), 2)
