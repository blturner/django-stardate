import datetime
import os
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from dateutil.parser import parse
from dropbox import client
from mock import Mock, patch
from social.apps.django_app.default.models import UserSocialAuth

from stardate.models import Blog
from stardate.parsers import FileParser
from stardate.backends.local_file import LocalFileBackend
from stardate.utils import get_post_model

Post = get_post_model()


def mock_get(path):
    return open(path)


def mock_put(path, content, overwrite):
    open(path, 'w').write(content)

    return {
        'path': path
    }


class StardateBackendTestCase(TestCase):
    def test_get_backend(self):
        from stardate.backends import get_backend

        backend_class = 'stardate.backends.local_file.LocalFileBackend'
        backend = get_backend(backend_class)

        self.assertIsInstance(backend, LocalFileBackend)


class DropboxBackendTestCase(TestCase):
    def setUp(self):
        file_path = tempfile.mkstemp(suffix='.txt', text=True)[1]

        user = User.objects.create(username='bturner')

        defaults = {
            "provider": "dropbox",
            "uid": "1234",
            "user": user,
            "extra_data": {
                "access_token": {
                    u'oauth_token_secret': u'oauth_token_secret_string',
                    u'oauth_token': u'oauth_token_string',
                    u'uid': u'123'
                }
            }
        }
        UserSocialAuth.objects.create(**defaults)

        blog = Blog.objects.create(
            name='Arbitrary',
            backend_class='stardate.backends.dropbox.DropboxBackend',
            backend_file=file_path,
            user=user,
        )

        self.blog = blog

    def tearDown(self):
        Blog.objects.all().delete()
        UserSocialAuth.objects.all().delete()
        User.objects.all().delete()

    def test_get_access_token(self):
        access_token = self.blog.backend.get_access_token()

        self.assertEqual(access_token['oauth_token_secret'], 'oauth_token_secret_string')
        self.assertEqual(access_token['oauth_token'], 'oauth_token_string')

    def test_cursor(self):
        self.assertEqual(self.blog.backend.get_cursor(), None)
        self.blog.backend.save_cursor('testing_cursor')
        self.assertEqual(self.blog.backend.get_cursor(), 'testing_cursor')

    def test_get_name(self):
        self.assertEqual(self.blog.backend.get_name(), 'dropbox')

    @patch.object(client.DropboxClient, 'delta', autospec=True)
    def test_delta(self, mock_delta):
        mock_delta.return_value = {
            'entries': [['/test_file.md']],
            'cursor': 'fake_cursor',
        }

        delta = self.blog.backend.delta()
        self.assertEqual(self.blog.backend.get_cursor(), 'fake_cursor')
        self.assertEqual(delta.get('entries')[0][0], '/test_file.md')

    @patch.object(client.DropboxClient, 'get_file')
    def test_get_file(self, mock_get_file):
        expected = 'title: Hello world\n\n\nHello world'

        mock_file = Mock()
        mock_file.read.return_value = expected
        mock_get_file.return_value = mock_file

        backend_file = self.blog.backend.get_file(self.blog.backend_file)

        self.assertEqual(backend_file, expected)

    @patch.object(client.DropboxClient, 'get_file')
    @patch.object(client.DropboxClient, 'put_file')
    def test_get_posts(self, mock_put_file, mock_get_file):
        mock_get_file.side_effect = mock_get
        mock_put_file.side_effect = mock_put

        Post.objects.create(
            title='Hello world',
            publish='2016-04-01 12:00:00+0000',
            body='Hello world.',
            blog=self.blog,
        )

        post_list = self.blog.backend.get_posts()

        self.assertEqual(len(post_list), 1)
        self.assertEqual(post_list[0]['title'], 'Hello world')
        self.assertEqual(post_list[0]['body'], 'Hello world.\n')
        self.assertEqual(
            post_list[0]['publish'],
            datetime.datetime(2016, 4, 1, 12, 0, tzinfo=timezone.utc)
        )

    @patch.object(client.DropboxClient, 'metadata')
    def test_get_source_list(self, mock_metadata):
        mock_metadata.return_value = {
            'modified': 'Wed, 20 Jul 2011 22:04:50 +0000',
            'hash': 'efdac89c4da886a9cece1927e6c22977',
            'contents': [
                {
                    'path': '/foo'
                },
                {
                    'path': '/bar'
                }
            ]
        }

        expected = (
            (0, '---'),
            (1, '/foo'),
            (2, '/bar'),
        )

        source_list = self.blog.backend.get_source_list()
        self.assertEqual(expected, source_list)

    @patch.object(client.DropboxClient, 'put_file')
    @patch.object(client.DropboxClient, 'get_file')
    @patch.object(client.DropboxClient, 'metadata')
    def test_pull(self, mock_metadata, mock_get_file, mock_put_file):
        post_string = 'title: Test post title\n\n\nHello world.'

        with open(self.blog.backend_file, 'w') as backend_file:
            backend_file.write(post_string)

        mock_get_file.side_effect = mock_get
        mock_put_file.side_effect = mock_put

        mock_metadata.return_value = {
            'modified': 'Wed, 20 Jul 2011 22:04:50 +0000',
        }

        pulled_posts = self.blog.backend.pull()
        self.assertEqual(len(pulled_posts), 1)
        self.assertEqual(pulled_posts[0].title, 'Test post title')

        # There should be no posts returned after the first update
        self.assertEqual(self.blog.backend.pull(), [])

    @patch.object(client.DropboxClient, 'put_file')
    @patch.object(client.DropboxClient, 'get_file')
    def test_push(self, mock_get_file, mock_put_file):
        mock_get_file.side_effect = mock_get
        mock_put_file.side_effect = mock_put

        # Creating a Post will automatically push it to the backend file
        first_post = Post.objects.create(
            blog=self.blog,
            title='Foo',
            body='Foo body.'
        )

        second_post = Post.objects.create(
            blog=self.blog,
            title='Bar',
            body='Bar body.'
        )

        backend_file = open(self.blog.backend_file).read()
        packed_string = self.blog.backend.parser.pack(
            [post.serialized() for post in self.blog.posts.all()]
        )
        self.assertEqual(backend_file, packed_string)

    @patch.object(client.DropboxClient, 'metadata')
    @patch.object(client.DropboxClient, 'get_file')
    @patch.object(client.DropboxClient, 'put_file')
    def test_pull_then_push(self, mock_put_file, mock_get_file, mock_metadata):
        mock_put_file.side_effect = mock_put
        mock_get_file.side_effect = mock_get
        mock_metadata.return_value = {
            'modified': 'Wed, 20 Jul 2011 22:04:50 +0000',
        }

        new_post = 'title: My test post\npublish: June 1, 2013 6AM PST\n\n\nPost body.\n'

        with open(self.blog.backend_file, 'w') as backend_file:
            backend_file.write(new_post)
            backend_file.close()

        self.blog.backend.pull()
        self.assertEqual(self.blog.posts.all().count(), 1)

        self.blog.backend.push(self.blog.posts.all())
        # # After push, file should have stardate metadata
        with open(self.blog.backend_file) as backend_file:
            self.assertTrue('stardate:' in backend_file.read())

        packed_string = self.blog.backend.parser.pack(
            [post.serialized() for post in self.blog.posts.all()]
        )
        self.assertEqual(
            self.blog.backend.client.get_file(self.blog.backend_file).read(),
            packed_string)

    def test_set_social_auth(self):
        user = User.objects.get(username='bturner')
        social_auth = UserSocialAuth.objects.get(user__exact=user.id)

        self.assertEqual(self.blog.backend.social_auth, social_auth)


class LocalFileBackendTestCase(TestCase):
    def setUp(self):
        fd, file_path = tempfile.mkstemp(suffix='.md')
        user = User.objects.create(username='bturner')
        blog = Blog.objects.create(
            backend_class='stardate.backends.local_file.LocalFileBackend',
            backend_file=file_path,
            name='arbitrary name',
            user=user,
        )
        Post.objects.create(
            blog=blog,
            title='Hello world',
            body='A very fine world it is.',
        )

        self.blog = blog
        self.post_list = blog.posts.all()

    def tearDown(self):
        Blog.objects.all().delete()
        Post.objects.all().delete()
        User.objects.all().delete()

    def test_is_mock_local_file_backend(self):
        self.assertIsInstance(self.blog.backend, LocalFileBackend)

    def test_get_name(self):
        self.assertEqual(self.blog.backend.get_name(), 'localfile')

    def test_get_post_path(self):
        serialized_posts = [post.serialized() for post in self.post_list]
        path = self.blog.backend._get_post_path('', serialized_posts[0])
        self.assertEqual(path, 'hello-world.md')
        path = self.blog.backend._get_post_path('posts', serialized_posts[0])
        self.assertEqual(path, 'posts/hello-world.md')

    def test_posts_from_file(self):
        temp_file = tempfile.mkstemp(suffix='.md')[1]
        f = open(temp_file, 'w')
        f.write('title: Test post\n\n\nThe body content.')
        f.close()

        self.blog.backend_file = temp_file

        posts = self.blog.backend.get_posts()
        self.assertEqual(posts, [{'title': 'Test post', 'body': 'The body content.'}])

    def test_posts_from_dir(self):
        temp_dir = tempfile.mkdtemp()
        fd, file_path = tempfile.mkstemp(dir=temp_dir, suffix='.md')
        f = open(file_path, 'w')
        f.write('title: Test post\n\n\nThe body content.')
        f.close()

        fd, file_path = tempfile.mkstemp(dir=temp_dir, suffix='.md')
        f = open(file_path, 'w')
        f.write('title: Another test post\n\n\nA different body.')
        f.close()

        self.blog.backend_file = temp_dir

        posts = self.blog.backend.get_posts()
        self.assertEqual(len(posts), 2)
        self.assertTrue('title' in posts[0])
        self.assertTrue('title' in posts[1])
        self.assertTrue('body' in posts[0])
        self.assertTrue('body' in posts[1])

        # cleanup temp files
        for f in os.listdir(temp_dir):
            f = os.path.join(temp_dir, f)
            os.remove(f)
        os.removedirs(temp_dir)

    def test_pull(self):
        timestamp = '2013-01-01 6:00 AM'
        expected_timestamp = datetime.datetime(2013, 1, 1, 11, 0, tzinfo=timezone.utc)

        f = open(self.blog.backend_file, 'w')
        f.write('title: Post title\npublish: {0}\ntimezone: US/Eastern\n\n\nA post for pulling in.'.format(timestamp))
        f.close()

        pulled_posts = self.blog.backend.pull()

        self.assertIsNotNone(pulled_posts[0].stardate)
        self.assertEqual(pulled_posts[0].title, 'Post title')
        self.assertEqual(pulled_posts[0].body.raw, 'A post for pulling in.\n')
        self.assertEqual(pulled_posts[0].publish, expected_timestamp)

    def test_push(self):
        Post.objects.create(
            title='A test push post',
            blog=self.blog,
            body='Testing a push post.'
        )

        f = open(self.blog.backend_file, 'r')
        content = f.read()
        f.close()

        parsed = self.blog.backend.parser.unpack(content)

        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[1]['title'], u'A test push post')
        self.assertEqual(parsed[1]['body'], u'Testing a push post.\n')
        self.assertTrue('stardate' in parsed[1])

    def test_disabled_blog(self):
        self.blog.sync = False
        self.blog.save()

        self.assertEqual(self.blog.backend.pull(), [])
        self.assertEqual(self.blog.backend.push({'title': 'Arbitrary title'}), [])
