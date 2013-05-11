from django.contrib.auth.models import User
from django.test import TestCase

from social_auth.models import UserSocialAuth

from stardate.backends.dropbox import DropboxBackend
from stardate.models import Blog
from stardate.tests.factories import create_blog, create_post, create_user, create_user_social_auth
from stardate.tests.mock_dropbox import MockDropboxClient


class DropboxBackendTestCase(TestCase):
    def setUp(self):
        self.backend = DropboxBackend()
        self.backend.client = MockDropboxClient()
        self.backend.client_class = MockDropboxClient

        social_auth = create_user_social_auth(user=create_user())
        self.backend.set_social_auth(social_auth)

        self.blog = create_blog()
        self.blog.backend.client_class = MockDropboxClient
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
        backend_file = self.backend.get_file('/test_file.md')
        self.assertEqual(backend_file, "publish: 2012-01-02 12:00 AM\ntitle: Tingling of the spine\n\n\nExtraordinary claims require extraordinary evidence!\n\n---\n\npublish: 2012-01-01 06:00 AM\ntitle: Great turbulent clouds\n\n\nWith pretty stories for which there's little good evidence.\n")

    def test_get_posts(self):
        post_list = self.backend.get_posts('/test_file.md')
        self.assertEqual(len(post_list), 2)
        self.assertEqual(post_list[0]['title'], 'Tingling of the spine')
        self.assertEqual(post_list[1]['title'], 'Great turbulent clouds')

    def test_get_source_list(self):
        source_list = self.backend.get_source_list()
        self.assertEqual(len(source_list), 3)

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
        post_list = self.blog.post_set.all()

        post_path = self.backend.get_post_path('posts', post_list[0])
        self.assertEqual(post_path, u'posts/test-post-title.md')

        # Try with no folder
        post_path = self.backend.get_post_path('', post_list[0])
        self.assertEqual(post_path, u'test-post-title.md')

    def test_serialize_posts(self):
        serialized_posts = self.backend.serialize_posts(self.blog.post_set.all())
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
