import datetime
import tempfile

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

try:
    from django.test.utils import override_settings
except ImportError:
    from django.test import override_settings

from dateutil import tz

from stardate.models import Blog, Post
from stardate.utils import get_post_model

from core.models import CustomPost


@override_settings(STARDATE_POST_MODEL='stardate.Post')
class BlogTestCase(TestCase):
    def setUp(self):
        file_path = tempfile.mkstemp(suffix='.txt', text=True)[1]
        user = User.objects.create(username='bturner')

        self.blog = Blog.objects.create(
            name='My test blog',
            backend_class='stardate.backends.local_file.LocalFileBackend',
            backend_file=file_path,
            user=user,
        )

        pub_date_1 = datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc)
        pub_date_2 = datetime.datetime(2012, 1, 3, 8, 0, tzinfo=timezone.utc)

        Post.objects.create(
            blog=self.blog,
            title="Test post 1 title",
            publish=pub_date_1
        )
        Post.objects.create(
            blog=self.blog,
            title="Test post 2 title",
            publish=pub_date_2
        )

    def tearDown(self):
        Blog.objects.all().delete()

    def test_blog_has_slug(self):
        self.assertTrue(self.blog.slug)
        self.assertEqual(self.blog.slug, 'my-test-blog')

    def test_get_post_model(self):
        self.assertIsInstance(get_post_model()(), Post)

        with self.settings(STARDATE_POST_MODEL='core.CustomPost'):
            self.assertIsInstance(get_post_model()(), CustomPost)

    def test_publish_field(self):
        post = Post(
            blog=self.blog,
            title='A starry night',
            publish=datetime.datetime(2016, 1, 1),
            timezone='US/Eastern',
            body='foo',
        )

        post.clean()

        expected = datetime.datetime(2016, 1, 1, tzinfo=tz.gettz('US/Eastern')).astimezone(timezone.utc)

        self.assertEqual(post.publish, expected)

    def test_get_serialized_posts(self):
        posts = self.blog.get_serialized_posts()
        self.assertEqual(len(posts), 2)

        self.assertTrue('stardate' in posts[0]['fields'])
        self.assertTrue('stardate' in posts[1]['fields'])

    def test_get_posts(self):
        post_list = self.blog.posts.all()
        self.assertTrue(len(post_list), 2)

    def test_get_next_post(self):
        first_post = Post.objects.get(title="Test post 1 title")
        self.assertEqual(first_post.title, "Test post 1 title")
        self.assertTrue(first_post.get_next_post())

        last_post = Post.objects.get(title="Test post 2 title")
        self.assertEqual(last_post.title, "Test post 2 title")
        self.assertFalse(last_post.get_next_post())

        self.assertEqual(first_post.get_next_post(), last_post)

    def test_get_prev_post(self):
        first_post = Post.objects.get(title="Test post 1 title")
        last_post = Post.objects.get(title="Test post 2 title")

        self.assertEqual(last_post.get_prev_post(), first_post)
        self.assertFalse(first_post.get_prev_post())

    def test_save_invalid_post(self):
        data = {
            'blog': self.blog
        }
        p = Post(**data)
        self.assertRaises(ValidationError, p.save)

    # def test_post_marked_deleted_is_removed(self):
    #     p = self.blog.posts.get(title="Test post title")
    #     p.mark_deleted()
    #     p.save()  # Probably bad
    #     self.assertTrue(p.deleted)
    #     self.assertTrue(self.blog.posts.get(title="Test post title").deleted)
    #     self.assertTrue(len(self.blog.get_serialized_posts()), 1)

    def test_removed_post_is_deleted(self):
        post_list = self.blog.get_serialized_posts()
        post_list.remove(post_list[0])
        self.assertTrue(len(post_list), 1)
