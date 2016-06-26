import datetime
import tempfile

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
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

    def test_drafts(self):
        Post.objects.create(blog=self.blog, title='Draft post')

        self.assertEqual(Post.objects.drafts().count(), 1)
        self.assertTrue(Post.objects.get(title='Draft post').is_draft)

    def test__unicode__(self):
        post = Post.objects.get(title='Test post 1 title')
        self.assertEqual(post.__str__(), u'Test post 1 title')

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

        post = Post.objects.get(id=1).serialized()
        self.assertTrue('stardate' in post)
        self.assertEqual(post['title'], 'Test post 1 title')
        self.assertEqual(post['publish'], '2012-01-02 08:00 AM +0000')
        self.assertEqual(post['timezone'], 'UTC')
        self.assertEqual(post['body'], '\n')

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

    def test_get_url_methods(self):
        post = Post.objects.get(title='Test post 1 title')

        self.assertEqual(post.get_absolute_url(), reverse('post-detail', kwargs={'blog_slug': post.blog.slug, 'post_slug': post.slug}))
        self.assertEqual(post.get_draft_url(), reverse('draft-post-detail', kwargs={'blog_slug': post.blog.slug, 'post_slug': post.slug}))

        self.assertEqual(
            post.get_dated_absolute_url(),
            reverse(
                'post-detail',
                kwargs={
                    'blog_slug': post.blog.slug,
                    'post_slug': post.slug,
                    'year': post.publish.year,
                    'month': post.publish.strftime('%b').lower(),
                    'day': post.publish.day,
                }
            )
        )

    def test_get_next_post(self):
        first_post = Post.objects.get(title="Test post 1 title")
        self.assertEqual(first_post.title, "Test post 1 title")
        self.assertTrue(first_post.get_next_post())

        last_post = Post.objects.get(title="Test post 2 title")
        self.assertEqual(last_post.title, "Test post 2 title")
        self.assertFalse(last_post.get_next_post())

        self.assertEqual(first_post.get_next_post(), last_post)

        Post.objects.create(blog=self.blog, title='draft')
        self.assertFalse(Post.objects.get(title='draft').get_next_post())
        self.assertFalse(Post.objects.get(title='draft').get_prev_post())

    def test_get_prev_post(self):
        first_post = Post.objects.get(title="Test post 1 title")
        last_post = Post.objects.get(title="Test post 2 title")

        self.assertEqual(last_post.get_prev_post(), first_post)
        self.assertFalse(first_post.get_prev_post())

    def test_creates_stardate_key(self):
        data = {
            'blog': self.blog,
            'title': 'Foo',
            'body': 'Foo bar.',
        }
        p = Post(**data)
        p.clean()
        self.assertTrue(p.stardate)

    def test_save_invalid_post(self):
        data = {
            'blog': self.blog
        }
        p = Post(**data)
        self.assertRaises(ValidationError, p.save)
