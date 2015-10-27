from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

# from stardate.feeds import LatestPostsFeed
from stardate.tests.factories import create_blog, create_post
from stardate.tests.mock_backends import MockDropboxClient
from stardate.utils import get_post_model


Post = get_post_model()


class LatestFeedTestCase(TestCase):
    def setUp(self):
        self.b = create_blog()
        self.b.backend.client_class = MockDropboxClient
        create_post(
            blog=self.b,
            body='# Headline\n\nAnd some text.\n'
        )
        self.client = Client()

    def test_feed(self):
        url = reverse('post-feed', kwargs={'blog_slug': self.b.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
