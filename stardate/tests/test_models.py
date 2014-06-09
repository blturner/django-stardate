import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from stardate.models import Blog
from stardate.tests.factories import create_blog, create_post
from stardate.utils import get_post_model

Post = get_post_model()


class BlogTestCase(TestCase):
    def setUp(self):
        self.blog = create_blog(
            name="My test blog",
            backend_class="stardate.tests.mock_backends.MockDropboxBackend",
        )

        pub_date_1 = datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc)
        pub_date_2 = datetime.datetime(2012, 1, 3, 8, 0, tzinfo=timezone.utc)
        create_post(blog=self.blog, publish=pub_date_1)
        create_post(blog=self.blog, title="Test post 2 title", publish=pub_date_2)

    def tearDown(self):
        Blog.objects.all().delete()

    def test_blog_has_slug(self):
        self.assertTrue(self.blog.slug)
        self.assertEqual(self.blog.slug, 'test-blog')

    def test_get_post_model(self):
        from core.models import Post as PostClass
        self.assertIsInstance(Post(), PostClass)

        with self.settings(STARDATE_POST_MODEL='stardate.CustomPost'):
            from core.models import CustomPost
            p = get_post_model()
            self.assertIsInstance(p(), CustomPost)

    def test_get_serialized_posts(self):
        posts = self.blog.get_serialized_posts()
        self.assertEqual(len(posts), 2)

    def test_get_posts(self):
        post_list = self.blog.get_posts()
        self.assertTrue(len(post_list), 2)

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

    def test_post_marked_deleted_is_removed(self):
        p = self.blog.get_posts().get(title="Test post title")
        p.mark_deleted()
        p.save()  # Probably bad
        self.assertTrue(p.deleted)
        self.assertTrue(self.blog.get_posts().get(title="Test post title").deleted)
        self.assertTrue(len(self.blog.get_serialized_posts()), 1)

    def test_removed_post_is_deleted(self):
        post_list = self.blog.get_serialized_posts()
        post_list.remove(post_list[0])
        self.assertTrue(len(post_list), 1)
