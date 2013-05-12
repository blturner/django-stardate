import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from social_auth.models import UserSocialAuth

from stardate.models import Blog
from stardate.parsers import FileParser
from stardate.tests.factories import create_blog, create_post
from stardate.tests.mock_backends import MockDropboxClient


class FileParserTestCase(TestCase):
    def setUp(self):
        self.parser = FileParser()
        self.test_string = "publish: 2012-01-02 12:00 AM\ntitle: Tingling of the spine\n\n\nExtraordinary claims require extraordinary evidence!"

    def tearDown(self):
        Blog.objects.all().delete()
        User.objects.all().delete()
        UserSocialAuth.objects.all().delete()

    def test_pack(self):
        blog = create_blog()
        blog.backend.client_class = MockDropboxClient
        create_post(title="First post", blog=blog)
        create_post(title="Second post", blog=blog)

        post_list = blog.get_serialized_posts()
        # packed = self.parser.pack(post_list)

        self.assertIsInstance(post_list, list)
        self.assertEqual(len(post_list), 2)
        # self.assertIsInstance(packed, basestring)

    def test_parse(self):
        parsed = self.parser.parse(self.test_string)

        self.assertEqual(parsed['title'], 'Tingling of the spine')
        self.assertEqual(parsed['publish'], datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc))
        self.assertEqual(parsed['body'], 'Extraordinary claims require extraordinary evidence!')

    def test_unpack(self):
        content = self.test_string
        post_list = self.parser.unpack(content)

        #The file has one post to unpack
        self.assertEqual(len(post_list), 1)
        self.assertEqual(post_list[0].get('title'), 'Tingling of the spine')
        self.assertEqual(post_list[0].get('publish'), datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc))
        self.assertEqual(post_list[0].get('body'), 'Extraordinary claims require extraordinary evidence!')
