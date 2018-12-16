import datetime
import os
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from dateutil.parser import parse
from dropbox import Dropbox
from mock import Mock, patch
from social_django.models import UserSocialAuth

from stardate.models import Blog
from stardate.parsers import FileParser
from stardate.backends.local_file import LocalFileBackend
from stardate.utils import get_post_model

Post = get_post_model()


def mock_get(path):
    tmp_file = open(path)
    mock_file = Mock()
    mock_file.content = tmp_file.read()

    return ('meta', mock_file)


def mock_put(content, path, mode):
    open(path, 'w').write(content)

    return {
        'path': path
    }


def mock_put_bytes(content, path, mode):
    open(path, 'wb').write(content)

    return {
        'path': path
    }


class MockMetadata:
    @property
    def server_modified(self):
        return parse('Wed, 20 Jul 2011 22:04:50 +0000')


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
            "provider": "dropbox-oauth2",
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

    @patch.object(Dropbox, 'files_download')
    def test_get_file(self, mock_get_file):
        expected = 'title: Hello world\n\n\nHello world'

        mock_file = Mock()
        mock_file.content = expected
        mock_get_file.return_value = ('metadata', mock_file)

        backend_file = self.blog.backend.get_file(self.blog.backend_file)

        self.assertEqual(backend_file, expected)

    @patch.object(Dropbox, 'files_download')
    @patch.object(Dropbox, 'files_upload')
    def test_get_posts(self, mock_put_file, mock_get_file):
        mock_get_file.side_effect = mock_get
        mock_put_file.side_effect = mock_put_bytes

        Post.objects.create(
            title='Hello world',
            publish=datetime.datetime(2016, 4, 1, 12),
            body='Hello world.',
            blog=self.blog,
        )

        post_list = self.blog.backend.get_posts()

        post = post_list[0]

        self.assertEqual(len(post_list), 1)
        self.assertEqual(post.get('title'), u'Hello world')
        self.assertEqual(post.content, u'Hello world.')

        self.assertEqual(
            post.get('publish'),
            datetime.datetime(2016, 4, 1, 12, 0, tzinfo=timezone.utc)
        )

    @patch.object(Dropbox, 'files_get_metadata')
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

    @patch.object(Dropbox, 'files_upload')
    @patch.object(Dropbox, 'files_download')
    @patch.object(Dropbox, 'files_get_metadata')
    def test_pull(self, mock_metadata, mock_get_file, mock_put_file):
        post_string = '---\ntitle: Test post title\n---\n\n\nHello world.\n{0}---\ntitle: Bar\npublish: 2016-01-01 00:00\n---\n\n\nBar.'.format(self.blog.backend.parser.delimiter)

        with open(self.blog.backend_file, 'w') as backend_file:
            backend_file.write(post_string)

        mock_get_file.side_effect = mock_get
        mock_put_file.side_effect = mock_put_bytes

        mock_metadata.return_value = MockMetadata()

        pulled_posts = self.blog.backend.pull()
        self.assertEqual(len(pulled_posts), 2)
        self.assertEqual(pulled_posts[0].title, 'Test post title')
        self.assertEqual(pulled_posts[1].title, 'Bar')

        # There should be no posts returned after the first update
        self.assertEqual(self.blog.backend.pull(), [])

    @patch.object(Dropbox, 'files_upload')
    @patch.object(Dropbox, 'files_download')
    @patch.object(Dropbox, 'files_get_metadata')
    def test_pull_with_dupe(self, mock_metadata, mock_get_file, mock_put_file):
        post_string = \
            '---\ntitle: Foo\n---\n\n\nHello world.\n{0}---\ntitle: Foo\n---\n\nBar.'.format(self.blog.backend.parser.delimiter)

        with open(self.blog.backend_file, 'w') as backend_file:
            backend_file.write(post_string)

        mock_get_file.side_effect = mock_get
        mock_put_file.side_effect = mock_put_bytes

        mock_metadata.return_value = MockMetadata()

        pulled_posts = self.blog.backend.pull()
        self.assertEqual(len(pulled_posts), 1)

    @patch.object(Dropbox, 'files_upload')
    @patch.object(Dropbox, 'files_download')
    def test_push(self, mock_get_file, mock_put_file):
        mock_get_file.side_effect = mock_get
        mock_put_file.side_effect = mock_put_bytes

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
        packed_string = self.blog.backend.parser.pack(self.blog.posts.all())
        self.assertEqual(backend_file, packed_string)

    @patch.object(Dropbox, 'files_get_metadata')
    @patch.object(Dropbox, 'files_download')
    @patch.object(Dropbox, 'files_upload')
    def test_pull_then_push(self, mock_put_file, mock_get_file, mock_metadata):
        mock_put_file.side_effect = mock_put_bytes
        mock_get_file.side_effect = mock_get
        mock_metadata.return_value = MockMetadata()

        new_post = '---\ntitle: My test post\npublish: June 1, 2013 6AM PST\n---\nPost body.\n'

        with open(self.blog.backend_file, 'w') as backend_file:
            backend_file.write(new_post)
            backend_file.close()

        self.blog.backend.pull()
        self.assertEqual(self.blog.posts.all().count(), 1)

        self.blog.backend.push(self.blog.posts.all())
        # # After push, file should have stardate metadata
        with open(self.blog.backend_file) as backend_file:
            self.assertTrue('stardate:' in backend_file.read())

        self.assertEqual(self.blog.posts.all().count(), 1)

        packed_string = self.blog.backend.parser.pack(self.blog.posts.all())

        _meta, file = self.blog.backend.client.files_download(self.blog.backend_file)

        self.assertEqual(file.content, packed_string)


class LocalFileBackendTestCase(TestCase):
    def setUp(self):
        self.fd, file_path = tempfile.mkstemp(suffix='.md')
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
        f.write('---\ntitle: Test post\n---\n\n\nThe body content.')
        f.close()

        self.blog.backend_file = temp_file

        posts = self.blog.backend.get_posts()

        # self.assertEqual(posts, [{'title': 'Test post', 'body': 'The body content.'}])
        self.assertEqual(posts[0].get('title'), 'Test post')
        self.assertEqual(posts[0].content, 'The body content.')

    def test_posts_from_dir(self):
        temp_dir = tempfile.mkdtemp()
        fd, file_path = tempfile.mkstemp(dir=temp_dir, suffix='.md')
        f = open(file_path, 'w')
        f.write('---\ntitle: Test post\n---\n\n\nThe body content.')
        f.close()

        fd, file_path = tempfile.mkstemp(dir=temp_dir, suffix='.md')
        f = open(file_path, 'w')
        f.write('---\ntitle: Another test post\n---\n\n\nA different body.')
        f.close()

        self.blog.backend_file = temp_dir

        posts = self.blog.backend.get_posts()
        self.assertEqual(len(posts), 2)

        first_post = [post for post in posts if post.get('title') == 'Test post']
        self.assertEqual(first_post[0].content, 'The body content.')

        second_post = [post for post in posts if post.get('title') == 'Another test post']
        self.assertEqual(second_post[0].content, 'A different body.')

        # cleanup temp files
        for f in os.listdir(temp_dir):
            f = os.path.join(temp_dir, f)
            os.remove(f)
        os.removedirs(temp_dir)

    def test_push_from_dir(self):
        temp_dir = tempfile.mkdtemp()
        fd, file_path = tempfile.mkstemp(dir=temp_dir, suffix='.md')
        f = open(file_path, 'w')
        f.write('---\ntitle: Test post\n---\n\n\nThe body content.')
        f.close()

        fd, file_path = tempfile.mkstemp(dir=temp_dir, suffix='.md')
        f = open(file_path, 'w')
        f.write('---\ntitle: Another test post\n---\n\n\nA different body.')
        f.close()

        self.blog.backend_file = temp_dir

        Post.objects.create(
            title='A test push post',
            blog=self.blog,
            publish=datetime.datetime(2016, 1, 1, 0, 0),
            body='Testing a push post.',
        )

        blog_files = os.listdir(temp_dir)
        new_file = open(os.path.join(temp_dir, blog_files[2]), 'r').read()

        self.assertEqual(len(blog_files), 3)
        self.assertTrue('A test push post' in new_file)
        self.assertTrue('---\n\nTesting a push post.' in new_file)
        self.assertTrue('publish: 2016-01-01 12:00 AM +0000' in new_file)
        
        # cleanup temp files
        for f in os.listdir(temp_dir):
            f = os.path.join(temp_dir, f)
            os.remove(f)
        os.removedirs(temp_dir)

    def test_pull(self):
        timestamp = '2013-01-01 6:00 AM'
        expected_timestamp = datetime.datetime(2013, 1, 1, 11, 0, tzinfo=timezone.utc)

        f = open(self.blog.backend_file, 'w')
        f.write('---\ntitle: Post title\npublish: {0}\ntimezone: US/Eastern\n---\n\n\nA post for pulling in.'.format(timestamp))
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
            publish=datetime.datetime(2016, 1, 1, 0, 0),
            body='Testing a push post.',
        )

        Post.objects.create(
            title='Foo',
            blog=self.blog,
            publish=datetime.datetime(2016, 2, 1, 0, 0),
            body='foo.',
        )

        f = open(self.blog.backend_file, 'r')
        content = f.read()
        f.close()

        self.assertEqual(content.count('---'), 6)

        self.assertTrue('title: A test push post' in content)
        self.assertTrue('publish: 2016-01-01 12:00 AM +0000' in content)
        self.assertTrue('\n\nTesting a push post.\n' in content)

        self.assertTrue('title: Foo' in content)
        self.assertTrue('publish: 2016-02-01 12:00 AM +0000' in content)
        self.assertTrue('\n\nfoo.' in content)

    def test_disabled_blog(self):
        self.blog.sync = False
        self.blog.save()

        self.assertEqual(self.blog.backend.pull(), [])
        self.assertEqual(self.blog.backend.push({'title': 'Arbitrary title'}), [])
