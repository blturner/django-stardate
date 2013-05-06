from __future__ import absolute_import

from django.conf import settings
from django.core.cache import cache

from dropbox import client, rest, session

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

    def _list_path(self, path='/', hash=None):
        """
        List the contents of a path on the backend. Each path can be passed
        a `hash` argument that determines if anything new for the specified
        path is returned.

        """
        paths = cache.get('paths', [])
        meta_hash = cache.get('hash', None)

        try:
            meta = self.client.metadata(path, hash=meta_hash)
            cache.delete('paths')
            cache.set('hash', meta['hash'])
        except rest.ErrorResponse, e:
            if e.status == 304:
                return paths
            raise e

        for content in meta.get('contents', []):
            paths.append(content['path'])
        cache.set('paths', paths)
        return paths

    def get_source_list(self):
        paths = cache.get('paths') or self._list_path()
        source_list = ((0, u'---'),)

        #  Instead of using the index, could use slugify
        try:
            for index, path in enumerate(paths):
                source_list += ((index + 1), path),
        except (AttributeError, TypeError):
            pass
        return source_list

    # pull
    def get_posts(self, path):
        """
        Gets a list of dictionaries of posts from the backend.

        """
        content = self.get_file(path)
        return self.parser.unpack(content)

    # push
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
