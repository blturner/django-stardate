import datetime
import os
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from dateutil.parser import parse
from mock import patch
from social.apps.django_app.default.models import UserSocialAuth

from stardate.models import Blog
from stardate.parsers import FileParser
from stardate.tests.factories import create_blog, create_post, create_user, \
    create_user_social_auth
from stardate.backends.local_file import LocalFileBackend
from stardate.tests.mock_backends import MockDropboxClient, \
    MockDropboxBackend
from stardate.utils import get_post_model

Post = get_post_model()


class StardateBackendTestCase(TestCase):
    def test_get_backend(self):
        from stardate.backends import get_backend

        backend_class = 'stardate.backends.local_file.LocalFileBackend'
        backend = get_backend(backend_class)

        self.assertIsInstance(backend, LocalFileBackend)


class DropboxBackendTestCase(TestCase):
    def setUp(self):
        self.patcher = patch('stardate.tests.mock_backends.MockDropboxClient.metadata')
        self.mock_metadata = self.patcher.start()

        self.mock_metadata.return_value = {
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

        backend_file, backend_file_path = tempfile.mkstemp(suffix='.txt')
        self.file_path = backend_file_path

        self.blog = create_blog(
            backend_class="stardate.tests.mock_backends.MockDropboxBackend",
            backend_file=backend_file_path
        )
        create_post(blog=self.blog)

        self.backend = self.blog.backend

    def tearDown(self):
        self.patcher.stop()

        Blog.objects.all().delete()
        UserSocialAuth.objects.all().delete()
        User.objects.all().delete()

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
        backend_file = self.backend.get_file(self.blog.backend_file)
        packed = self.backend.parser.pack(self.blog.backend.get_posts())
        self.assertEqual(backend_file, packed)

    def test_get_file_changed(self):
        backend_file_path = self.blog.backend_file
        self.backend.client.put_file(backend_file_path, 'new string')
        self.assertEqual(self.backend.get_file(backend_file_path), 'new string')

    def test_get_posts(self):
        post_list = self.blog.backend.get_posts()
        self.assertEqual(len(post_list), 1)
        self.assertEqual(post_list[0]['title'], 'Test post title')

    def test_get_source_list(self):
        source_list = self.backend.get_source_list()
        self.assertEqual(len(source_list), 3)

    def test_pull(self):
        blog = self.blog
        pulled_posts = blog.backend.pull()
        self.assertEqual(len(pulled_posts), 1)
        self.assertEqual(pulled_posts[0].title, 'Test post title')

    def test_push(self):
        create_post(blog=self.blog, title="Test one")
        create_post(blog=self.blog, title="Test two")
        self.blog.backend.push(self.blog.posts.all())

        backend_file = self.backend.get_file(self.blog.backend_file)
        packed_string = self.backend.parser.pack(
            [post.serialized() for post in self.blog.posts.all()]
        )
        self.assertEqual(backend_file, packed_string)

    def test_pull_then_push(self):
        test_string = 'title: My test post\npublish: June 1, 2013 6AM PST\n\n\nPost body.\n'
        self.backend.client.put_file(self.blog.backend_file, test_string)
        self.assertEqual(
            self.backend.client.get_file(self.blog.backend_file).read(),
            test_string)
        for post in self.blog.posts.all():
            post.delete()
        self.assertFalse(self.blog.posts.all())
        
        self.blog.backend.pull()
        self.assertEqual(len(self.blog.posts.all()), 1)
        self.blog.backend.push(self.blog.posts.all())
        # After push, file should have stardate metadata
        packed_string = self.backend.parser.pack(
            [post.serialized() for post in self.blog.posts.all()]
        )
        self.assertEqual(
            self.backend.client.get_file(self.blog.backend_file).read(),
            packed_string)

    def test_pull_then_pull(self):
        test_string = 'title: Title\n\n\nBody.\n'
        self.backend.client.put_file(self.blog.backend_file, test_string)

        for post in self.blog.posts.all():
            post.delete()

        self.assertEqual(len(self.blog.backend.pull()), 1)
        self.assertEqual(len(self.blog.backend.pull()), 0)

    def test_push_blog_file(self):
        posts = self.blog.posts.all()
        self.blog.backend.push_blog_file(posts)
        f = open(self.blog.backend_file, 'r')

        packed_string = self.backend.parser.pack(
            [post.serialized() for post in self.blog.posts.all()]
        )

        self.assertEqual(f.read(), packed_string)

    def test_save_cursor(self):
        self.backend.save_cursor('test_cursor')
        self.assertEqual(self.backend.cursor, 'test_cursor')

    def test_set_social_auth(self):
        user = User.objects.get(username='bturner')
        social_auth = UserSocialAuth.objects.get(user__exact=user.id)

        self.assertEqual(self.backend.social_auth, social_auth)


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
        timestamp = '2013-01-01 6:00 AM EST'
        parsed_timestamp = datetime.datetime(2013, 1, 1, 11, 0, tzinfo=timezone.utc)

        f = open(self.blog.backend_file, 'w')
        f.write('title: Post title\npublish: {0}\n\n\nA post for pulling in.'.format(timestamp))
        f.close()

        pulled_posts = self.blog.backend.pull()

        self.assertIsNotNone(pulled_posts[0].stardate)
        self.assertEqual(pulled_posts[0].title, 'Post title')
        self.assertEqual(pulled_posts[0].body.raw, 'A post for pulling in.\n')
        self.assertEqual(pulled_posts[0].publish.astimezone(timezone.utc),
                         parsed_timestamp.replace(tzinfo=timezone.utc))

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
