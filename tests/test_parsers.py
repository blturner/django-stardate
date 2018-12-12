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
        self.test_string = "---\npublish: {0}\ntimezone: US/Eastern\ntitle: Tingling of the spine\n---\nExtraordinary claims require extraordinary evidence!".format(TIMESTAMP)

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
            sync=False,
        )

        p1 = Post.objects.create(
            blog=blog,
            title='My first post',
            publish=datetime.datetime(2015, 1, 1, 6, 0),
            body='This is the first post.'
        )

        p2 = Post.objects.create(
            blog=blog,
            title='My second post',
            publish=datetime.datetime(2015, 1, 2, 6, 0),
            body='This is the second post.'
        )

        post_list = blog.posts.all()

        packed = self.parser.pack(post_list)

        self.assertEqual(len(post_list), 2)

        try:
            self.assertIsInstance(packed, basestring)
        except NameError:
            self.assertIsInstance(packed, str)

        self.assertTrue(u'title: {0}'.format(p1.title) in packed)
        self.assertTrue(u'title: {0}'.format(p2.title) in packed)

        self.assertTrue(u'stardate: {0}'.format(p1.stardate) in packed)
        self.assertTrue(u'stardate: {0}'.format(p2.stardate) in packed)

        self.assertTrue(u'{0}'.format(p1.body.raw.strip()) in packed)
        self.assertTrue(u'{0}'.format(p2.body.raw.strip()) in packed)

        p1_publish = datetime.datetime.strftime(
            p1.publish,
            '%Y-%m-%d %I:%M %p %z'
        )
        self.assertTrue(u'publish: {0}'.format(p1_publish) in packed)

        p2_publish = datetime.datetime.strftime(
            p2.publish,
            '%Y-%m-%d %I:%M %p %z'
        )
        self.assertTrue(u'publish: {0}'.format(p2_publish) in packed)

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

        self.assertEqual(
            self.parser.parse_publish(datetime.datetime(2016, 1, 1, 0, 0, tzinfo=timezone.utc), 'US/Eastern'),
            datetime.datetime(2016, 1, 1, tzinfo=tz.gettz('US/Eastern'))
        )

    def test_parse(self):
        expected = datetime.datetime(2012, 1, 2, tzinfo=tz.gettz('US/Eastern'))
        parsed = self.parser.parse(self.test_string)

        self.assertEqual(parsed.metadata.get('title'), u'Tingling of the spine')
        self.assertEqual(parsed.metadata.get('timezone'), u'US/Eastern')
        
        # self.assertEqual(parsed['publish'], expected)
        self.assertEqual(parsed.content, u'Extraordinary claims require extraordinary evidence!')

    def test_unpack(self):
        content = self.test_string
        post_list = self.parser.unpack(content)
        post = post_list[0]

        self.assertEqual(len(post_list), 1)
        self.assertEqual(post.get('title'), u'Tingling of the spine')
        self.assertEqual(
            self.parser.parse_publish(post.get('publish'), post.get('timezone')),
            datetime.datetime(2012, 1, 2, tzinfo=tz.gettz('US/Eastern'))
        )
        self.assertEqual(
            post.content,
            u'Extraordinary claims require extraordinary evidence!'
        )

    @patch('stardate.parsers.logger')
    def test_bad_string(self, mock_logging):
        content = 'bad string\n\r'
        posts = self.parser.unpack(content)

        self.assertEqual(posts, [])
        mock_logging.warn.assert_called_once_with(
            'Not enough information found to parse string.')
