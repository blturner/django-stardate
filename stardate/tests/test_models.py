from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from social_auth.models import UserSocialAuth

from stardate.models import Blog, Post
from stardate.tests.mock_dropbox import MockDropboxClient


class BlogTestCase(TestCase):
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
        }
        defaults.update(kwargs)
        return Post.objects.create(**defaults)

    def test_get_serialized_posts(self):
        user = self.create_user()
        blog = self.create_blog(name="My test blog", owner=user)
        blog.backend.client_class = MockDropboxClient

        self.create_post(blog=blog)
        self.create_post(blog=blog, title="Test post 2 title")

        posts = blog.get_serialized_posts()
        self.assertEqual(len(posts), 2)

    # def test_get_next_post(self):
    #     p = Post.objects.get(pk=1)
    #     self.assertFalse(p.get_next_post())

    #     p = Post.objects.get(pk=2)
    #     self.assertEqual(p.get_next_post().pk, 1)

    # def test_get_prev_post(self):
    #     p = Post.objects.get(pk=1)
    #     self.assertEqual(p.get_prev_post().pk, 2)

    #     p = Post.objects.get(pk=2)
    #     self.assertFalse(p.get_prev_post())

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
