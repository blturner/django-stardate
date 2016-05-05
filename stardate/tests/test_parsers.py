import datetime
import pytz
import tempfile
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from dateutil import tz
from dateutil.parser import parse
from mock import patch

from stardate.models import Blog, Post
from stardate.parsers import FileParser


TIMESTAMP = '2012-01-02 12:00 AM'


class FileParserTestCase(TestCase):
    def setUp(self):
        self.parser = FileParser()
        self.test_string = "publish: {0}\ntimezone: US/Eastern\ntitle: Tingling of the spine\n\n\nExtraordinary claims require extraordinary evidence!".format(TIMESTAMP)

    def tearDown(self):
        Blog.objects.all().delete()
        User.objects.all().delete()

    def test_pack(self):
        file_path = tempfile.mkstemp(suffix='.txt')[1]
        user = User.objects.create(username='bturner')
        blog = Blog.objects.create(
            backend_file=file_path,
            backend_class='stardate.backends.local_file.LocalFileBackend',
            name='test blog',
            user=user,
        )

        Post.objects.create(
            blog=blog,
            title='My first post',
            publish=datetime.datetime(2015, 1, 1, 6, 0),
            body='This is the first post.'
        )

        Post.objects.create(
            blog=blog,
            title='My second post',
            publish=datetime.datetime(2015, 1, 2, 6, 0),
            body='This is the second post.'
        )

        post_list = [post.serialized() for post in blog.posts.all()]

        packed = self.parser.pack(post_list)

        self.assertIsInstance(post_list, list)
        self.assertEqual(len(post_list), 2)
        self.assertIsInstance(packed, basestring)

        self.assertTrue(u'title: {0}'.format(post_list[0]['title']) in packed)
        self.assertTrue(u'title: {0}'.format(post_list[1]['title']) in packed)
        self.assertTrue(u'stardate: {0}'.format(post_list[0]['stardate']) in packed)
        self.assertTrue(u'stardate: {0}'.format(post_list[1]['stardate']) in packed)
        self.assertTrue(u'\n\n\n{0}'.format(post_list[0]['body']) in packed)
        self.assertTrue(u'\n\n\n{0}'.format(post_list[1]['body']) in packed)
        self.assertTrue(u'publish: {0}'.format(post_list[0]['publish']) in packed)
        self.assertTrue(u'publish: {0}'.format(post_list[1]['publish']) in packed)

    def test_parse_publish(self):
        timestamp = '01-01-2015 06:00AM+0000'
        expected = datetime.datetime(2015, 1, 1, 6, 0, tzinfo=timezone.utc)

        self.assertEqual(self.parser.parse_publish(timestamp), expected)
        self.assertEqual(self.parser.parse_publish(expected), expected)

        self.assertEqual(
            self.parser.parse_publish('2016-01-01 00:00:00 -0500'),
            datetime.datetime(2016, 1, 1, tzinfo=tz.gettz('US/Eastern'))
        )

        self.assertEqual(
            self.parser.parse_publish('2016-01-01'),
            datetime.datetime(2016, 1, 1, tzinfo=timezone.utc)
        )

        self.assertEqual(
            self.parser.parse_publish('2016-01-01 00:00:00'),
            datetime.datetime(2016, 1, 1, tzinfo=timezone.utc)
        )

        self.assertEqual(
            self.parser.parse_publish('2016-01-01 12AM', 'US/Eastern'),
            datetime.datetime(2016, 1, 1, tzinfo=tz.gettz('US/Eastern'))
        )

        self.assertEqual(
            self.parser.parse_publish(datetime.date(2016, 1, 1)),
            datetime.datetime(2016, 1, 1, tzinfo=timezone.utc)
        )

        self.assertEqual(
            self.parser.parse_publish('2016-01-01 12AM', 'EST'),
            datetime.datetime(2016, 1, 1, tzinfo=tz.gettz('US/Eastern'))
        )

        self.assertEqual(
            self.parser.parse_publish('2016-07-01 12AM', 'US/Eastern'),
            datetime.datetime(2016, 7, 1, tzinfo=tz.gettz('US/Eastern'))
        )

    def test_parse(self):
        parsed = self.parser.parse(self.test_string)

        self.assertEqual(parsed['title'], 'Tingling of the spine')
        expected = datetime.datetime(2012, 1, 2, tzinfo=tz.gettz('US/Eastern'))
        self.assertEqual(parsed['publish'], expected)
        self.assertEqual(parsed['body'], 'Extraordinary claims require extraordinary evidence!')
        self.assertEqual(parsed['timezone'], 'US/Eastern')

        # Check that extra_field is parsed
        string = u"title: My title\nextra_field: Something arbitrary\n\n\nThe body.\n"
        parsed = self.parser.parse(string)
        self.assertTrue(parsed.has_key('title'))
        self.assertTrue(parsed.has_key('extra_field'))

    def test_render(self):
        post = Post(
            title='Test title',
            publish=datetime.datetime(2013, 6, 1),
            timezone='US/Eastern',
            body='The body.',
        )

        post.clean()

        packed = self.parser.pack([post.serialized()])
        rendered = self.parser.render(post.serialized())

        self.assertEqual(rendered, packed)

    def test_unpack(self):
        content = self.test_string
        post_list = self.parser.unpack(content)

        #The file has one post to unpack
        self.assertEqual(len(post_list), 1)

        post = post_list[0]

        self.assertEqual(post.get('title'), 'Tingling of the spine')

        self.assertEqual(
            post.get('publish'),
            datetime.datetime(2012, 1, 2, tzinfo=tz.gettz('US/Eastern'))
        )

        self.assertEqual(post.get('body'), 'Extraordinary claims require extraordinary evidence!')

    @patch('stardate.parsers.logger')
    def test_bad_string(self, mock_logging):
        content = 'bad string\n\r'
        posts = self.parser.unpack(content)

        self.assertEqual(posts, [])
        mock_logging.warn.assert_called_once_with(
            'Not enough information found to parse string.')
