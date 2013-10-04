import datetime
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from social_auth.models import UserSocialAuth

from stardate.models import Blog
from stardate.parsers import FileParser
from stardate.tests.factories import create_blog
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
        post_list = [
            {
                'title': 'My first post',
                'created': datetime.datetime.now(),
                'stardate': uuid.uuid1(),
                'body': 'This is the first post.'
            },
            {
                'title': 'My second post',
                'created': datetime.datetime.now(),
                'stardate': uuid.uuid1(),
                'body': 'This is the second post.'
            },
        ]
        packed_string = self.parser.pack(post_list)

        self.assertIsInstance(post_list, list)
        self.assertEqual(len(post_list), 2)
        self.assertIsInstance(packed_string, basestring)
        self.assertEqual(packed_string, "stardate: %s\ncreated: %s\ntitle: My first post\n\n\nThis is the first post.\n---\nstardate: %s\ncreated: %s\ntitle: My second post\n\n\nThis is the second post." % (post_list[0]['stardate'], post_list[0]['created'], post_list[1]['stardate'], post_list[1]['created']))

    def test_parse(self):
        parsed = self.parser.parse(self.test_string)

        self.assertEqual(parsed['title'], 'Tingling of the spine')
        self.assertEqual(parsed['publish'], datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc))
        self.assertEqual(parsed['body'], 'Extraordinary claims require extraordinary evidence!')

    def test_render(self):
        test_stardate = uuid.uuid1()
        dict_to_render = {
            'body': 'The body.',
            'publish': datetime.datetime(2013, 6, 1, 0, 0),
            'stardate': test_stardate,
            'title': 'Test title',
        }
        dict_without_publish = dict_to_render.copy()
        dict_without_publish.pop('publish', None)

        string = 'stardate: %s\ntitle: Test title\npublish: 2013-06-01 00:00:00\n\n\nThe body.' % test_stardate
        rendered = self.parser.render(dict_to_render)
        self.assertEqual(rendered, string)

        string = 'stardate: %s\ntitle: Test title\n\n\nThe body.' % test_stardate
        rendered = self.parser.render(dict_without_publish)
        self.assertEqual(rendered, string)

    def test_unpack(self):
        content = self.test_string
        post_list = self.parser.unpack(content)

        #The file has one post to unpack
        self.assertEqual(len(post_list), 1)
        self.assertEqual(post_list[0].get('title'), 'Tingling of the spine')
        self.assertEqual(post_list[0].get('publish'), datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc))
        self.assertEqual(post_list[0].get('body'), 'Extraordinary claims require extraordinary evidence!')
