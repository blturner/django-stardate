from django.db import IntegrityError
from django.test import TestCase

from stardate.models import Blog, Post


class BlogTestCase(TestCase):
    fixtures = ['stardate_parser_testdata.json']

    def setUp(self):
        super(BlogTestCase, self).setUp()
        self.blog = Blog.objects.get(pk=1)

    def test_get_serialized_posts(self):
        posts = self.blog.get_serialized_posts()
        # fields = posts[0].get('fields')

        self.assertEqual(len(posts), 2)

    def test_get_next_post(self):
        p = Post.objects.get(pk=1)
        self.assertFalse(p.get_next_post())

        p = Post.objects.get(pk=2)
        self.assertEqual(p.get_next_post().pk, 1)

    def test_get_prev_post(self):
        p = Post.objects.get(pk=1)
        self.assertEqual(p.get_prev_post().pk, 2)

        p = Post.objects.get(pk=2)
        self.assertFalse(p.get_prev_post())

    def test_invalid_publish(self):
        data = {
            'title': 'A duplicate publish date',
            'publish': '2012-01-01T14:00:00Z',
        }
        data['blog_id'] = 1
        p = Post(**data)
        self.assertRaises(IntegrityError, p.save)
