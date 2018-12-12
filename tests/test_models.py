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

from tests.models import CustomPost


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
            sync=False,
        )

        pub_date_1 = datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc)
        pub_date_2 = datetime.datetime(2012, 1, 3, 8, 0, tzinfo=timezone.utc)

        Post.objects.create(
            blog=self.blog,
            title="Test post 1 title",
            publish=pub_date_1,
            body='the post content',
        )
        Post.objects.create(
            blog=self.blog,
            title="Test post 2 title",
            publish=pub_date_2,
            body='the other post content',
        )

    def tearDown(self):
        Blog.objects.all().delete()

    def test_blog_user(self):
        user = User.objects.get(username='bturner')

        self.assertEqual(len(user.blogs.all()), 1)
        self.assertEqual(self.blog.user, user)

    def test_blog_has_slug(self):
        self.assertTrue(self.blog.slug)
        self.assertEqual(self.blog.slug, 'my-test-blog')

    def test_get_post_model(self):
        self.assertIsInstance(get_post_model()(), Post)

        with self.settings(STARDATE_POST_MODEL='tests.CustomPost'):
            self.assertIsInstance(get_post_model()(), CustomPost)

    def test_serialized_posts(self):
        serialized = [post.serialized() for post in self.blog.posts.all()]
        self.assertEqual(len(serialized), 2)

        post = serialized[1]
        self.assertTrue('stardate' in post)
        self.assertEqual(post['title'], 'Test post 1 title')
        self.assertEqual(post['publish'], '2012-01-02 08:00 AM +0000')
        self.assertEqual(post['timezone'], 'UTC')
        self.assertEqual(post['body'], 'the post content\n')

    def test_publish_field(self):
        post = Post.objects.create(
            blog=self.blog,
            title='A starry night',
            publish=datetime.date(2016, 1, 1),
            timezone='US/Eastern',
            body='foo',
        )

        expected = datetime.datetime(2016, 1, 1, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(timezone.is_aware(post.publish))
        self.assertEqual(post.publish, expected)

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
