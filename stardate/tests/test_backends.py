import datetime
import os
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from social.apps.django_app.default.models import UserSocialAuth

from stardate.models import Blog
from stardate.parsers import FileParser
from stardate.tests.factories import create_blog, create_post, create_user, \
    create_user_social_auth
from stardate.tests.mock_backends import MockDropboxClient, \
    MockDropboxBackend, MockLocalFileBackend
from stardate.utils import get_post_model

Post = get_post_model()


class DropboxBackendTestCase(TestCase):
    def setUp(self):
        backend_file, backend_file_path = tempfile.mkstemp(suffix='.txt')
        self.file_path = backend_file_path
        self.backend = MockDropboxBackend()
        social_auth = create_user_social_auth(user=create_user())
        self.backend.set_social_auth(social_auth)

        self.blog = create_blog(
            backend_class="stardate.tests.mock_backends.MockDropboxBackend",
            backend_file=backend_file_path
        )
        create_post(blog=self.blog)

    def tearDown(self):
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
        packed = self.backend.parser.pack(self.backend.get_posts(self.file_path))
        self.assertEqual(backend_file, packed)

    def test_get_file_changed(self):
        backend_file_path = self.blog.backend_file
        self.backend.client.put_file(backend_file_path, 'new string')
        self.assertEqual(self.backend.get_file(backend_file_path), 'new string')

    def test_get_posts(self):
        post_list = self.backend.get_posts(self.blog.backend_file)
        self.assertEqual(len(post_list), 1)
        self.assertEqual(post_list[0]['title'], 'Test post title')

    def test_get_source_list(self):
        source_list = self.backend.get_source_list()
        self.assertEqual(len(source_list), 3)

    def test_pull(self):
        blog = self.blog
        pulled_posts = blog.backend.pull(blog)
        self.assertEqual(len(pulled_posts), 1)
        self.assertEqual(pulled_posts[0].title, 'Test post title')

    def test_push(self):
        create_post(blog=self.blog, title="Test one")
        create_post(blog=self.blog, title="Test two")
        self.blog.backend.push(self.blog.get_posts().all())

        backend_file = self.backend.get_file(self.blog.backend_file)
        packed_string = self.backend.parser.pack(
            self.backend.serialize_posts(self.blog.get_posts().all()))
        self.assertEqual(backend_file, packed_string)

    def test_pull_then_push(self):
        test_string = 'title: My test post\npublish: June 1, 2013\n\n\nPost body.\n'
        self.backend.client.put_file(self.blog.backend_file, test_string)
        self.assertEqual(
            self.backend.client.get_file(self.blog.backend_file).read(),
            test_string)
        for post in self.blog.get_posts().all():
            post.delete()
        self.assertFalse(self.blog.get_posts().all())
        self.backend.pull(self.blog)
        self.assertEqual(len(self.blog.get_posts().all()), 1)
        self.backend.push(self.blog.get_posts().all())
        # After push, file should have stardate metadata
        packed_string = self.backend.parser.pack(
            self.backend.serialize_posts(self.blog.get_posts().all()))
        self.assertEqual(
            self.backend.client.get_file(self.blog.backend_file).read(),
            packed_string)

    def test_pull_then_pull(self):
        test_string = 'title: Title\n\n\nBody.\n'
        self.backend.client.put_file(self.blog.backend_file, test_string)
        for post in self.blog.get_posts().all():
            post.delete()
        self.backend.pull(self.blog)
        self.backend.pull(self.blog)

    def test_push_then_pull(self):
        pass

    def test_push_blog_file(self):
        posts = self.blog.get_posts().all()
        self.backend.push_blog_file(self.blog.backend_file, posts)
        f = open(self.blog.backend_file, 'r')
        packed_string = self.backend.parser.pack(
            self.backend.serialize_posts(self.blog.get_posts().all()))
        self.assertEqual(f.read(), packed_string)

    # def test_push_blog_files(self):
    #     self.assertEqual(1, 2)


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

    def test_get_post_path(self):
        post_list = self.blog.get_posts().all()

        post_path = self.backend.get_post_path('posts', post_list[0])
        self.assertEqual(post_path, u'posts/test-post-title.md')

        # Try with no folder
        post_path = self.backend.get_post_path('', post_list[0])
        self.assertEqual(post_path, u'test-post-title.md')

    def test_serialize_posts(self):
        serialized_posts = self.backend.serialize_posts(self.blog.get_posts().all())
        self.assertIn('title', serialized_posts[0])
        self.assertIn('stardate', serialized_posts[0])
        self.assertIn('publish', serialized_posts[0])
        self.assertIn('body', serialized_posts[0])

    # def test_sync(self):
    #     user = User.objects.get(username='bturner')
    #     blog = create_blog(owner=user)
    #     blog.backend.client_class = MockDropboxClient
    #     create_post(blog=blog)
    #     post_list = blog.post_set.all()

    #     sync = self.backend.sync(post_list)

    #     self.assertEqual(sync.read(), 'stardate: 352b967d-87bf-11e2-81f3-b88d120c8298\npublish: 2013-01-04 12:00 AM\ntitle: Fourth post\n\n\nDo it.\n')


class LocalFileBackendTestCase(TestCase):
    def setUp(self):
        fd, file_path = tempfile.mkstemp(suffix='.md')
        self.blog = create_blog(
            backend_class="stardate.tests.mock_backends.MockLocalFileBackend",
            backend_file=file_path)
        create_post(title="Hello world", blog=self.blog)

        self.post_list = self.blog.get_posts().all()

    def tearDown(self):
        Blog.objects.all().delete()
        Post.objects.all().delete()
        User.objects.all().delete()
        UserSocialAuth.objects.all().delete()

    def test_is_mock_local_file_backend(self):
        self.assertIsInstance(self.blog.backend, MockLocalFileBackend)

    def test_get_name(self):
        self.assertEqual(self.blog.backend.get_name(), 'localfile')

    def test_get_post_path(self):
        serialized_posts = self.blog.backend.serialize_posts(
            self.post_list)
        path = self.blog.backend._get_post_path('', serialized_posts[0])
        self.assertEqual(path, 'hello-world.md')
        path = self.blog.backend._get_post_path('posts', serialized_posts[0])
        self.assertEqual(path, 'posts/hello-world.md')

    def test_posts_from_file(self):
        temp_file = tempfile.mkstemp(suffix='.md')[1]
        f = open(temp_file, 'w')
        f.write('title: Test post\n\n\nThe body content.')
        f.close()

        posts = self.blog.backend.get_posts(temp_file)
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

        posts = self.blog.backend.get_posts(temp_dir)
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
        temp_dir = tempfile.mkdtemp()
        fd, file_path = tempfile.mkstemp(dir=temp_dir, suffix='.md')
        blog = create_blog(name='Pull',
                           backend_class='stardate.tests.mock_backends.MockLocalFileBackend',
                           backend_file=file_path,
                           slug='pull')

        f = open(file_path, 'w')
        f.write('title: Post title\npublish: 2013-01-01 6:00 AM\n\n\nA post for pulling in.')
        f.close()

        pulled_posts = blog.backend.pull(blog)

        self.assertIsNotNone(pulled_posts[0].stardate)
        self.assertEqual(pulled_posts[0].title, 'Post title')
        self.assertEqual(pulled_posts[0].body.raw, 'A post for pulling in.\n')
        self.assertEqual(pulled_posts[0].publish, datetime.datetime(2013, 1, 1, 14, 0, tzinfo=timezone.utc))

    def test_push(self):
        fd, file_path = tempfile.mkstemp(suffix='.md')
        blog = create_blog(name='Push',
                           backend_class='stardate.tests.mock_backends.MockLocalFileBackend',
                           backend_file=file_path,
                           slug='push')

        # creating a post calls `push`
        create_post(title='A test push post', blog=blog, body='Testing a push post.')

        f = open(file_path, 'r')
        content = f.read()
        parser = FileParser()
        parsed = parser.unpack(content)
        self.assertEqual(parsed[0]['title'], u'A test push post')
        self.assertEqual(parsed[0]['body'], u'Testing a push post.\n')
        self.assertTrue('stardate' in parsed[0])

    def test_serialize_posts(self):
        serialized_posts = self.blog.backend.serialize_posts(self.post_list)
        self.assertIn('title', serialized_posts[0])
        self.assertIn('created', serialized_posts[0])
        self.assertIn('stardate', serialized_posts[0])
        self.assertIn('publish', serialized_posts[0])
        self.assertIn('body', serialized_posts[0])
