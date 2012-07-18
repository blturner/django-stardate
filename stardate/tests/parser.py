import datetime

from django.test import TestCase
from django.utils import timezone
from dropbox import client
from mock import patch

from stardate.dropbox_auth import DropboxAuth
from stardate.models import Blog, DropboxFile, Post
from stardate.parser import Stardate


class StardateTestCase(TestCase):
    fixtures = ['stardate_parser_testdata.json']

    def setUp(self):
        super(StardateTestCase, self).setUp()

        self.unparsed_db_file = DropboxFile.objects.get(pk=1)
        self.parsed_db_file = DropboxFile.objects.get(pk=2)
        self.blog = Blog.objects.get(pk=1)
        self.time_zone = timezone.get_default_timezone()

        self.stardate = Stardate()

    def test_stardate_parse(self):
        c = self.blog.dropbox_file.content
        result = self.stardate.parse(c)

        title = result[0].get('title')
        publish = result[0].get('publish')
        body = result[0].get('body')

        # The returned list should contain 2 posts.
        self.assertEqual(len(result), 2)

        # Assert that the expected values are parsed.
        self.assertEqual(title, u'Tingling of the spine')
        self.assertEqual(publish, datetime.datetime(2012, 1, 2, 0, 0, tzinfo=timezone.get_current_timezone()))
        self.assertEqual(body, u'Extraordinary claims require extraordinary evidence!\n')

    @patch.object(client.DropboxClient, 'put_file')
    @patch.object(DropboxAuth, 'get_dropbox_client')
    def test_stardate_parse_publish(self, mock_put_file, mock_get_dropbox_client):
        text = "title: Testing publish\npublish: 2012-01-01 07:00 AM\n\nTest content.\n"
        post_data = self.stardate.parser.parse_post(text)
        post_data['blog_id'] = self.blog.id
        p = Post.objects.create(**post_data)
        p.clean()
        p.save()

        serialized_data = self.blog.get_serialized_posts()
        for post in serialized_data:
            if post.get('fields')['title'] == u'Testing publish':
                self.assertTrue(timezone.is_aware(post.get('fields')['publish']))
                # January 1, 2012 7:00 AM PST should convert to January 1, 2012 3:00 PM UTC
                self.assertEqual(post.get('fields')['publish'], datetime.datetime(2012, 1, 1, 15, 0, tzinfo=timezone.utc))
                # January 1, 2012 3:00 PM UTC should convert to January 1, 2012 7:00 AM PST
                self.assertEqual(datetime.datetime.strftime(post.get('fields')['publish'].astimezone(self.time_zone), '%Y-%m-%d %I:%M %p %Z'), u'2012-01-01 07:00 AM PST')

    def test_parse_post(self):
        text = "title: Another world\npublish: 2012-01-02 12:00 AM\n\nGathered by gravity, not a sunrise but a galaxyrise hydrogen atoms.\n"
        result = self.stardate.parser.parse_post(text)
        title = result.get('title')
        publish = result.get('publish')
        body = result.get('body')

        self.assertEqual(len(result), 3)
        self.assertEqual(title, u'Another world')
        self.assertTrue(timezone.is_aware(publish))
        self.assertEqual(publish, datetime.datetime(2012, 1, 2, 0, 0, tzinfo=self.time_zone))
        self.assertEqual(body, u'Gathered by gravity, not a sunrise but a galaxyrise hydrogen atoms.\n')

    def test_parse_post_no_publish(self):
        text = "title: Another world\n\nContent.\n"
        result = self.stardate.parser.parse_post(text)

        self.assertTrue(result.get('title'))
        self.assertTrue(result.get('body'))
        self.assertFalse(result.get('publish'))

    def test_parse_post_invalid_publish(self):
        text = u'title: A broken post\npublish: 2012-01-02 14:00:00+00:00\n\nContent.\n'
        result = self.stardate.parser.parse_post(text)

        self.assertEqual(result.get('publish'), datetime.datetime(2012, 1, 2, 14, 0))

    @patch.object(client.DropboxClient, 'put_file')
    @patch.object(DropboxAuth, 'get_dropbox_client')
    def test_import_multiple_posts(self, mock_put_file, mock_get_dropbox_client):
        self.blog.dropbox_file = DropboxFile.objects.get(pk=2)

        posts = self.stardate.parse(self.blog.dropbox_file.content)
        for post in posts:
            post['blog_id'] = self.blog.id
            try:
                p = Post.objects.get(stardate=post.get('stardate'))
            except Post.DoesNotExist:
                p = Post(**post)
            p.clean()
            p.save()

            self.assertTrue(p.stardate)
            self.assertTrue(p.slug)

        self.assertEqual(self.blog.post_set.count(), 2)

        self.blog.dropbox_file.content = self.stardate.parse_for_dropbox(self.blog.get_serialized_posts())
        self.blog.dropbox_file.content = "title: A new post\n\nSome new content.\n\n---\n\ntitle: A funny thing happened\n\nOn my walk today.\n\n---\n\n" + self.blog.dropbox_file.content

        posts = self.stardate.parse(self.blog.dropbox_file.content)
        for post in posts:
            post['blog_id'] = self.blog.id
            try:
                p = Post.objects.get(stardate=post.get('stardate'))
            except Post.DoesNotExist:
                p = Post(**post)

            p.__dict__.update(**post)
            p.clean()
            p.save()

            self.assertTrue(p.body)

        self.assertEqual(self.blog.post_set.count(), 4)
        self.blog.dropbox_file.content = self.stardate.parse_for_dropbox(self.blog.get_serialized_posts())

        for post in self.blog.post_set.all():
            self.assertIsNotNone(post.body)
