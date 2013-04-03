from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from stardate.models import Blog, Post
from stardate.tests.mock_dropbox import MockDropboxClient


# class MockStardateSync(StardateSync):
#     def __init__(self, *args, **kwargs):
#         self.client = MockDropboxClient()
#         self.dropbox_client = self.client
#         super(StardateSync, self).__init__()


# class DropboxFileTestCase(TestCase):
#     fixtures = ['stardate_parser_testdata.json']

#     def setUp(self):
#         super(DropboxFileTestCase, self).setUp()
#         self.dropbox_file = DropboxFile.objects.get(pk=1)

#     def test_sync_to_dropbox(self):
#         user = User.objects.get(pk=1)
#         auth = user.social_auth.get(provider='dropbox')
#         self.dropbox_file.content = 'new content'
#         self.assertEqual(self.dropbox_file.sync_to_dropbox(auth,
#             sync_class=MockStardateSync).read(), 'new content')


class BlogTestCase(TestCase):
    fixtures = ['stardate_parser_testdata.json']

    def setUp(self):
        super(BlogTestCase, self).setUp()
        self.blog = Blog.objects.get(pk=1)

    def test_get_serialized_posts(self):
        posts = self.blog.get_serialized_posts()

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

    # def test_save_stardate_posts_sets_post_deleted(self):
    #     df = DropboxFile.objects.get(pk=1)
    #     df.content = "stardate: 9df753dc-c87f-11e1-ba83-b88d120c8298\npublish: 2012-01-02 12:00 AM\ntitle: Tingling of the spine\n\n\nExtraordinary claims require extraordinary evidence!\n"

    #     self.blog.dropbox_file = df

    #     parser = Stardate()
    #     parsed = parser.parse(df.content)

    #     deleted_posts = self.blog.mark_deleted_posts(parsed)

    #     self.assertEqual(deleted_posts.__len__(), 2)

    #     for post in deleted_posts:
    #         self.assertTrue(post.deleted)

    def test_save_invalid_post(self):
        data = {
            'blog': Blog.objects.get(pk=1)
        }
        p = Post(**data)
        self.assertRaises(ValidationError, p.save)

    def test_invalid_publish(self):
        data = {
            'title': 'A duplicate publish date',
            'publish': '2012-01-01T14:00:00Z',
        }
        data['blog_id'] = 1
        p = Post(**data)
        self.assertRaises(ValidationError, p.save)
