import datetime
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from social.apps.django_app.default.models import UserSocialAuth

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
        packed = self.parser.pack(post_list)

        self.assertIsInstance(post_list, list)
        self.assertEqual(len(post_list), 2)
        self.assertIsInstance(packed, basestring)

        self.assertTrue(u'title: {0}'.format(post_list[0]['title']) in packed)
        self.assertTrue(u'title: {0}'.format(post_list[1]['title']) in packed)
        self.assertTrue(u'created: {0}'.format(post_list[0]['created']) in packed)
        self.assertTrue(u'created: {0}'.format(post_list[1]['created']) in packed)
        self.assertTrue(u'stardate: {0}'.format(post_list[0]['stardate']) in packed)
        self.assertTrue(u'stardate: {0}'.format(post_list[1]['stardate']) in packed)
        self.assertTrue(u'\n\n\n{0}'.format(post_list[0]['body']) in packed)
        self.assertTrue(u'\n\n\n{0}'.format(post_list[1]['body']) in packed)

    def test_parse(self):
        parsed = self.parser.parse(self.test_string)

        self.assertEqual(parsed['title'], 'Tingling of the spine')
        self.assertEqual(parsed['publish'], datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc))
        self.assertEqual(parsed['body'], 'Extraordinary claims require extraordinary evidence!')

        # Check that extra_field is parsed
        string = u"title: My title\nextra_field: Something arbitrary\n\n\nThe body.\n"
        parsed = self.parser.parse(string)
        self.assertTrue(parsed.has_key('title'))
        self.assertTrue(parsed.has_key('extra_field'))

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

        packed = self.parser.pack([dict_to_render])
        rendered = self.parser.render(dict_to_render)
        self.assertEqual(packed, rendered)

        packed = self.parser.pack([dict_without_publish])
        rendered = self.parser.render(dict_without_publish)
        self.assertEqual(packed, rendered)

        dict_to_render['extra_field'] = u'Something arbitrary'
        rendered = self.parser.render(dict_to_render)
        packed = self.parser.pack([dict_to_render])
        self.assertEqual(rendered, packed)
        self.assertTrue('extra_field: Something arbitrary\n' in rendered)

    def test_unpack(self):
        content = self.test_string
        post_list = self.parser.unpack(content)

        #The file has one post to unpack
        self.assertEqual(len(post_list), 1)
        self.assertEqual(post_list[0].get('title'), 'Tingling of the spine')
        self.assertEqual(post_list[0].get('publish'), datetime.datetime(2012, 1, 2, 8, 0, tzinfo=timezone.utc))
        self.assertEqual(post_list[0].get('body'), 'Extraordinary claims require extraordinary evidence!')
