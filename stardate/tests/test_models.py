import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from social_auth.models import UserSocialAuth

from stardate.models import Blog, Post
from stardate.tests.mock_dropbox import MockDropboxClient


class BlogTestCase(TestCase):
    def setUp(self):
        user = self.create_user()
        self.blog = self.create_blog(name="My test blog", owner=user)
        self.blog.backend.client_class = MockDropboxClient

        pub_date = datetime.datetime(2012, 1, 3, 8, 0, tzinfo=timezone.utc)
        self.create_post(blog=self.blog)
        self.create_post(blog=self.blog, title="Test post 2 title", publish=pub_date)

    def create_user(self, **kwargs):
        defaults = {
            "username": "bturner",
        }
        return User.objects.create(
            **defaults)

    def create_user_social_auth(self, **kwargs):
        defaults = {
            "provider": "dropbox",
            "uid": "1234",
            "user": kwargs['user'],
            "extra_data": {"access_token": "oauth_token_secret=oauth_token_secret_string&oauth_token=oauth_token_string"}
        }
        defaults.update(kwargs)
        return UserSocialAuth.objects.create(**defaults)

    def create_blog(self, **kwargs):
        defaults = {
            "name": "Test blog",
            "backend_file": "0",
            "social_auth": self.create_user_social_auth(
                user=kwargs['owner'])
        }
        defaults.update(kwargs)
        if "owner" not in defaults:
            defaults["owner"] = self.create_user()
        return Blog.objects.create(
            **defaults)

    def create_post(self, **kwargs):
        defaults = {
            "blog": kwargs['blog'],
            "body": "Test post body.",
            "title": "Test post title",
            "publish": datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc),
        }
        defaults.update(kwargs)
        return Post.objects.create(**defaults)

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

    # def test_save_invalid_post(self):
    #     data = {
    #         'blog': self.blog
    #     }
    #     p = Post(**data)
    #     self.assertRaises(ValidationError, p.save)

    # def test_invalid_publish(self):
    #     data = {
    #         'title': 'A duplicate publish date',
    #         'publish': '2012-01-01T14:00:00Z',
    #     }
    #     data['blog_id'] = 1
    #     p = Post(**data)
    #     self.assertRaises(ValidationError, p.save)
