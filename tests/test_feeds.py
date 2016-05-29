import tempfile

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from stardate.models import Blog, Post
from stardate.utils import get_post_model


Post = get_post_model()


class LatestFeedTestCase(TestCase):
    def setUp(self):
        file_path = tempfile.mkstemp(suffix='.txt')[1]
        user = User.objects.create(username='bturner')

        blog = Blog.objects.create(
            backend_class='stardate.backends.local_file.LocalFileBackend',
            backend_file=file_path,
            name='Feeds',
            slug='feeds',
            user=user,
        )

        Post.objects.create(
            blog=blog,
            title='Hello world',
            body='My blog post.',
        )

    def test_feed(self):
        url = reverse('post-feed', kwargs={'blog_slug': 'feeds'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
