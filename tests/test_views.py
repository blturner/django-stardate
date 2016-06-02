import hmac
import json

from hashlib import sha256

from django.core.urlresolvers import reverse
from django.test import Client, TestCase, override_settings

SECRET_KEY = '123456'.encode('utf-8')
URL = reverse('webhook')


class TestViews(TestCase):
    def setUp(self):
        self.client = Client()

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
