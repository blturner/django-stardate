from __future__ import absolute_import

from django.conf import settings
from django.core.cache import cache

from dropbox import client, session

from stardate.backends import StardateBackend
from stardate.parsers import SingleFileParser


APP_KEY = getattr(settings, 'DROPBOX_APP_KEY', None)
APP_SECRET = getattr(settings, 'DROPBOX_APP_SECRET', None)
ACCESS_TYPE = getattr(settings, 'DROPBOX_ACCESS_TYPE', None)


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
        delta = self.client.delta(cursor=self.cursor)
        self.save_cursor(delta.get('cursor'))
        return delta

    def get_file(self, path):
        return self.client.get_file(path).read()

    def has_update(self):
        """
        Returns True if new data is available on the server.

        """
        return self.delta().get('has_more')

    def _list_path(self, path='/', hash=None):
        """
        List the contents of a path on the backend. Each path can be passed
        a `hash` argument that determines if anything new for the specified
        path is returned.

        [
            '/path/file.txt',
            '/path/folder/file.txt',
        ]

        """
        try:
            meta = self.client.metadata(path, hash=hash)
        except:
            return
        path_list = []

        for content in meta['contents']:
            if content['is_dir']:
                path_list += self._list_path(path=content['path'])
            path_list.append(content['path'])
        return path_list

    def get_source_list(self):
        source_list = ()

        for index, path in enumerate(self._list_path()):
            source_list += (index, path),
        return source_list

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

    def get_posts(self, path):
        """
        Gets a list of dictionaries of posts from the backend.

        """
        content = self.get_file(path)
        return self.parser.unpack(content)

    def put_posts(self, path, post_list):
        """
        Puts stringified collections of posts on the backend.

        """
        if post_list:
            content = self.parser.pack(post_list)
            return self.client.put_file(path, content, overwrite=True)
        else:
            print u'No post_list'

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
