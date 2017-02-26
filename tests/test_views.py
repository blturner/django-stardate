import hmac
import json
import tempfile

from hashlib import sha256

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase, override_settings

from stardate.models import Blog, Post

SECRET_KEY = '123456'.encode('utf-8')
URL = reverse('webhook')


class TestViews(TestCase):
    def setUp(self):
        file_path = tempfile.mkstemp(suffix='.txt', text=True)[1]
        self.client = Client()

        user = User.objects.create_user(username='bturner', password='123')

        self.blog = Blog.objects.create(
            user=user,
            name='stardate',
            backend_class='stardate.backends.local_file.LocalFileBackend',
            backend_file=file_path,
        )

    def tearDown(self):
        User.objects.all().delete()
        Blog.objects.all().delete()

    def test_create_view(self):
        self.client.login(username='bturner', password='123')

        resp = self.client.get(reverse('blog-create', kwargs={'provider': 'local'}))

        self.assertEqual(resp.status_code, 200)

    def test_post_create(self):
        self.client.login(username='bturner', password='123')

        resp = self.client.get(
            reverse(
                'post-create',
                kwargs={
                    'blog_slug': self.blog.slug
                }
            )
        )

        self.assertEqual(resp.status_code, 200)

    def test_can_create_post(self):
        self.client.login(username='bturner', password='123')

        resp = self.client.post(
            reverse(
                'post-create',
                kwargs={
                    'blog_slug': self.blog.slug
                }
            ),
            {
                'title': 'my post',
                'body': 'my post body',
            }
        )

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('post-detail', kwargs={'blog_slug': self.blog.slug, 'post_slug': 'my-post'}))
        self.assertTrue(Post.objects.get(title='my post'))

    def test_post_archive_index(self):
        self.client.login(username='bturner', password='123')

        resp = self.client.get(
            reverse(
                'post-archive-index',
                kwargs={
                    'blog_slug': 'stardate'
                }
            )
        )

        self.assertEqual(resp.status_code, 200)

    def test_draft_archive_index(self):
        self.client.login(username='bturner', password='123')

        resp = self.client.get(
            reverse(
                'draft-archive-index',
                kwargs={
                    'blog_slug': 'stardate'
                }
            )
        )

        self.assertEqual(resp.status_code, 200)

    def test_draft_post_detail(self):
        Post.objects.create(title='draft', blog=self.blog)

        self.client.login(username='bturner', password='123')

        resp = self.client.get(
            reverse(
                'draft-post-detail',
                kwargs={
                    'post_slug': 'draft',
                    'blog_slug': self.blog.slug,
                }
            )
        )

        self.assertEqual(resp.status_code, 200)

    def test_draft_post_edit(self):
        Post.objects.create(title='draft', blog=self.blog)

        self.client.login(username='bturner', password='123')

        resp = self.client.get(
            reverse(
                'draft-post-edit',
                kwargs={
                    'post_slug': 'draft',
                    'blog_slug': self.blog.slug,
                }
            )
        )

        self.assertEqual(resp.status_code, 200)

    def test_process_webhook_get_request(self):
        resp = self.client.get(URL, {'challenge': u'abc'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'abc')

        resp = self.client.get(URL)
        self.assertEqual(resp.status_code, 403)

    @override_settings(DROPBOX_APP_SECRET=SECRET_KEY)
    def test_process_webhook_post_request(self):
        data = {
            'delta': {
                'users': [
                    123,
                    456,
                ]
            }
        }

        signature = generate_signature(SECRET_KEY, json.dumps(data))

        resp = self.client.post(
            URL,
            json.dumps(data),
            content_type='application/json',
            HTTP_X_DROPBOX_SIGNATURE=signature
        )
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(
            URL,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 403)

def generate_signature(secret, message):
    secret = bytes(secret)
    try:
        message = bytes(message)
    except TypeError:
        message = bytes(message, 'utf-8')

    return hmac.new(secret, message, sha256).hexdigest()
