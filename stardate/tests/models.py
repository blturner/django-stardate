from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from mock import patch

from stardate.models import Blog, DropboxFile, Post
from stardate.sync import StardateSync
from stardate.tests.sync import MockDropboxClient


class MockStardateSync(StardateSync):
    def __init__(self, *args, **kwargs):
        self.client = MockDropboxClient
        StardateSync.__init__(self, *args, **kwargs)


class DropboxFileTestCase(TestCase):
    fixtures = ['stardate_parser_testdata.json']

    def setUp(self):
        super(DropboxFileTestCase, self).setUp()
        self.dropbox_file = DropboxFile.objects.get(pk=1)

    @patch.object(StardateSync, 'get_dropbox_client')
    def test_sync_to_dropbox(self, mock_method):
        mock_method.return_value = MockDropboxClient()

        user = User.objects.get(pk=1)
        auth = user.social_auth.get(provider='dropbox')
        self.dropbox_file.content = 'new content'
        self.assertEqual(self.dropbox_file.sync_to_dropbox(auth).read(), 'new content')


class BlogTestCase(TestCase):
    fixtures = ['stardate_parser_testdata.json']

    def setUp(self):
        super(BlogTestCase, self).setUp()
        self.blog = Blog.objects.get(pk=1)

    def test_get_serialized_posts(self):
        posts = self.blog.get_serialized_posts()

        self.assertEqual(len(posts), 2)

    def test_get_next_post(self):
        p = Post.objects.get(pk=1)
        self.assertFalse(p.get_next_post())

        p = Post.objects.get(pk=2)
        self.assertEqual(p.get_next_post().pk, 1)

    def test_get_prev_post(self):
        p = Post.objects.get(pk=1)
        self.assertEqual(p.get_prev_post().pk, 2)

        p = Post.objects.get(pk=2)
        self.assertFalse(p.get_prev_post())

    @patch.object(StardateSync, 'get_dropbox_client')
    def test_save_post(self, mock_get_dropbox_client):
        mock_get_dropbox_client.return_value = MockDropboxClient()

        data = {
            'title': 'Test post',
            'body': 'This is the content.',
            'blog': Blog.objects.get(pk=1)
        }
        p = Post(**data)
        p.save()

        saved_post = Post.objects.get(title='Test post')
        self.assertEqual(saved_post.title, 'Test post')
        self.assertEqual(saved_post.body, 'This is the content.\n')

    def test_save_invalid_post(self):
        data = {
            'blog': Blog.objects.get(pk=1)
        }
        p = Post(**data)
        self.assertRaises(ValidationError, p.save)

    def test_invalid_publish(self):
        data = {
            'title': 'A duplicate publish date',
            'publish': '2012-01-01T14:00:00Z',
        }
        data['blog_id'] = 1
        p = Post(**data)
        self.assertRaises(ValidationError, p.save)
