from django.test import TestCase

from stardate.models import Blog, Post


# class BlogTestCase(TestCase):
#     fixtures = ['stardate_parser_testdata.json']

#     def setUp(self):
#         super(BlogTestCase, self).setUp()
#         self.blog = Blog.objects.get(pk=1)

#     def test_get_serialized_posts(self):
#         self.assertTrue(1 + 1, 2)
