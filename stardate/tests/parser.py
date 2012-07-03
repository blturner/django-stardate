import datetime

# from django.core.management import call_command
from django.test import TestCase

from stardate.models import Blog, DropboxFile, Post
from stardate.parser import Stardate


class StardateTestCase(TestCase):
    fixtures = ['stardate_parser_testdata.json']

    def setUp(self):
        super(StardateTestCase, self).setUp()

        self.dropbox_file = DropboxFile.objects.get(pk=2)
        self.stardate = Stardate()
        self.result = self.stardate.parse(self.dropbox_file.content)
        self.parsed_post = self.result[0]

    def test_stardate_parse(self):
        title = self.result[0].get('title')
        publish = self.result[0].get('publish')
        body = self.result[0].get('body')

        # The returned list should contain 2 posts.
        self.assertEqual(len(self.result), 2)

        # Assert that the expected values are parsed.
        self.assertEqual(title, u'Gathered by gravity')
        self.assertEqual(publish, datetime.datetime(2012, 2, 2, 4, 0))
        self.assertEqual(body, u'Gathered by gravity, not a sunrise but a galaxyrise hydrogen atoms.\n')

    def test_parse_post(self):
        text = "title: Another world\npublish: 2012-01-02 12:00 AM\n\nGathered by gravity, not a sunrise but a galaxyrise hydrogen atoms.\n"
        result = self.stardate.parser.parse_post(text)
        title = result.get('title')
        publish = result.get('publish')
        body = result.get('body')

        self.assertEqual(len(result), 3)
        self.assertEqual(title, u'Another world')
        self.assertEqual(publish, datetime.datetime(2012, 1, 2, 0, 0))
        self.assertEqual(body, u'Gathered by gravity, not a sunrise but a galaxyrise hydrogen atoms.\n')

    def test_import_multiple_posts(self):
        blog = Blog(name="Test", slug="test", dropbox_file=self.dropbox_file)
        blog.save()

        posts = self.stardate.parse(blog.dropbox_file.content)
        for post in posts:
            post['blog_id'] = blog.id
            p = Post.objects.create(**post)
            p.clean()
            p.save()

            self.assertTrue(p.stardate)
            self.assertTrue(p.slug)

        self.assertEqual(blog.post_set.count(), 2)

        blog.dropbox_file.content = self.stardate.parse_for_dropbox(blog.get_serialized_posts())
        blog.dropbox_file.content = "title: A new post\n\nSome new content.\n\n---\n\ntitle: A funny thing happened\n\nOn my walk today.\n\n---\n\n" + blog.dropbox_file.content

        posts = self.stardate.parse(blog.dropbox_file.content)
        for post in posts:
            post['blog_id'] = blog.id
            try:
                p = Post.objects.get(stardate=post.get("stardate"))
            except Post.DoesNotExist:
                p = Post(**post)

            p.__dict__.update(**post)
            p.clean()
            p.save()

            self.assertTrue(p.body)

        self.assertEqual(blog.post_set.count(), 4)
        blog.dropbox_file.content = self.stardate.parse_for_dropbox(blog.get_serialized_posts())

        for post in blog.post_set.all():
            self.assertIsNotNone(post.body)
