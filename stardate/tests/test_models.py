import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone


from stardate.models import Blog, Post
from stardate.tests.factories import create_blog, create_post
from stardate.tests.mock_dropbox import MockDropboxClient


class BlogTestCase(TestCase):
    def setUp(self):
        self.blog = create_blog(name="My test blog")
        self.blog.backend.client_class = MockDropboxClient

        pub_date_1 = datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc)
        pub_date_2 = datetime.datetime(2012, 1, 3, 8, 0, tzinfo=timezone.utc)
        create_post(blog=self.blog, publish=pub_date_1)
        create_post(blog=self.blog, title="Test post 2 title", publish=pub_date_2)

    def tearDown(self):
        Blog.objects.all().delete()

    def test_get_serialized_posts(self):
        posts = self.blog.get_serialized_posts()
        self.assertEqual(len(posts), 2)

    def test_get_next_post(self):
        first_post = Post.objects.get(title="Test post title")
        self.assertEqual(first_post.title, "Test post title")
        self.assertTrue(first_post.get_next_post())

        last_post = Post.objects.get(title="Test post 2 title")
        self.assertEqual(last_post.title, "Test post 2 title")
        self.assertFalse(last_post.get_next_post())

        self.assertEqual(first_post.get_next_post(), last_post)

    def test_get_prev_post(self):
        first_post = Post.objects.get(title="Test post title")
        last_post = Post.objects.get(title="Test post 2 title")

        self.assertEqual(last_post.get_prev_post(), first_post)
        self.assertFalse(first_post.get_prev_post())

    def test_save_invalid_post(self):
        data = {
            'blog': self.blog
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
