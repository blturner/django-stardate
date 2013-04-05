from __future__ import absolute_import

from django.conf import settings
from django.core.cache import cache

from dropbox import client, session

from stardate.backends import StardateAdapter, StardateBackend
from stardate.parsers import SingleFileParser


APP_KEY = getattr(settings, 'DROPBOX_APP_KEY', None)
APP_SECRET = getattr(settings, 'DROPBOX_APP_SECRET', None)
ACCESS_TYPE = getattr(settings, 'DROPBOX_ACCESS_TYPE', None)


class DropboxAdapter(StardateAdapter):
    def get_client(self):
        return self.backend.get_dropbox_client()


class DropboxBackend(StardateBackend):
    def __init__(self, client_class=client.DropboxClient):
        self.client = None
        self.client_class = client_class
        self.cursor = self.get_cursor()
        self.name = u'dropbox'
        self.parser = SingleFileParser()
        self.social_auth = None

    def get_access_token(self):
        bits = {}
        token = self.social_auth.extra_data['access_token']
        for bit in token.split('&'):
            b = bit.split('=')
            bits[b[0]] = b[1]
        return bits

    def get_cursor(self):
        try:
            cursor = self.social_auth.extra_data['cursor']
        except (AttributeError, KeyError):
            cursor = None
        return cursor

    def get_dropbox_client(self):
        try:
            sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
            token = self.get_access_token()
            sess.set_token(token['oauth_token'], token['oauth_token_secret'])
            return self.client_class(sess)
        except AttributeError, e:
            print e

    def get_name(self):
        return self.name

    def delta(self):
        return self.client.delta(cursor=self.cursor)

    def get_file(self, path):
        return self.client.get_file(path).read()

    def get_file_list(self):
        """
        Returns a list of iterables: [(1, '/test.md')]
        """
        key_name = 'dropbox_file_list'
        timeout = 60 * 5

        file_list = cache.get(key_name)
        if file_list is not None:
            return file_list

        file_list = []
        try:
            entries = self.delta().get('entries')

            for i, entry in enumerate(entries):
                file_path = entry[0]
                metadata = entry[1]
                if metadata and not metadata.get('is_dir'):
                    file_list.append((i, file_path))
        except:
            pass
        cache.set(key_name, file_list, timeout)
        return file_list

    def get_content(self, path):
        return self.client.get_file(path).read()

    def get_posts(self, path):
        content = self.get_content(path)
        return self.parser.unpack(content)

    def save_cursor(self, cursor):
        self.social_auth.extra_data['cursor'] = cursor
        self.social_auth.save()
        self.cursor = self.get_cursor()

    def set_social_auth(self, social_auth):
        self.social_auth = social_auth
        self.client = self.get_dropbox_client()

    def sync(self, path, post_list):
        """
        Expects a list of post dictionaries to convert to a string and
        put on the backend.
        """
        content = self.parser.pack(post_list)
        return self.client.put_file(path, content, overwrite=True)
