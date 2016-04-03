from __future__ import absolute_import
import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

from dateutil.parser import parse

from dropbox import client, rest, session

from stardate.backends import StardateBackend
from stardate.parsers import FileParser

def get_settings_or_env(var_name):
    """
    Get a setting from the settings file or an env variable
    """
    value = getattr(settings, var_name, None)
    if not value:
        try:
            return os.environ[var_name]
        except KeyError:
            error_msg = "Could not find setting or ENV variable {0}".format(var_name)
            raise ImproperlyConfigured(error_msg)
    return value

APP_KEY = get_settings_or_env('DROPBOX_APP_KEY')
APP_SECRET = get_settings_or_env('DROPBOX_APP_SECRET')
ACCESS_TYPE = get_settings_or_env('DROPBOX_ACCESS_TYPE')

logger = logging.getLogger('stardate')


class DropboxBackend(StardateBackend):
    def __init__(self, client_class=client.DropboxClient, *args, **kwargs):
        super(DropboxBackend, self).__init__(*args, **kwargs)
        self.client = None
        self.client_class = client_class
        self.cursor = self.get_cursor()
        self.name = u'dropbox'
        self.parser = FileParser()
        self.social_auth = None

        self.set_social_auth(self.blog.social_auth)

    def get_file(self, path):
        return self.client.get_file(path).read()

    def write_file(self, file_path, content):
        return self.client.put_file(file_path, content, overwrite=True)

    def get_post(self, path):
        try:
            content = self.get_file(path)
            post = self.parser.parser(post)
        except Exception:
            post = {}
        return post

    def get_access_token(self):
        return self.social_auth.extra_data['access_token']

    def get_cursor(self):
        try:
            cursor = self.social_auth.extra_data['cursor']
        except (AttributeError, KeyError):
            cursor = None
        return cursor

    def get_dropbox_client(self):
        sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
        token = self.get_access_token()
        sess.set_token(token['oauth_token'], token['oauth_token_secret'])
        return self.client_class(sess)

    def delta(self):
        delta = self.client.delta(cursor=self.cursor)
        self.save_cursor(delta.get('cursor'))
        return delta

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

    def save_cursor(self, cursor):
        self.social_auth.extra_data['cursor'] = cursor
        self.social_auth.save()
        self.cursor = self.get_cursor()

    def set_social_auth(self, social_auth):
        self.social_auth = social_auth
        self.client = self.get_dropbox_client()

    def get_post_path(self, folder, post):
        """
        Dynamically guess post file path from slug / blog folder
        """
        filename = post.slug
        filename = '{0}.md'.format(filename)
        path = os.path.join(folder, filename)
        return path

    def push_post_files(self, blog_dir, posts):
        """
        Update posts in multiple files
        """
        responses = []
        for post in posts:
            # Generate the post file path dynamically
            post_path = self.get_post_path(blog_dir, post)

            # Get the existing remote post as a post dict
            try:
                remote_post = self.client.get_file(post_path).read()
            except Exception:
                remote_post = {}
            remote_post = self.parser.parse(remote_post)

            # Turn local post into post dict
            local_post = self.serialize_posts([post])[0]


            # Update the contents of the remote post
            remote_post.update(local_post)
            content = self.parser.render(remote_post)
            response = self.client.put_file(post_path, content, overwrite=True)

            # Log the result
            responses.append(response)
        return responses

    def get_posts(self):
        """
        Fetch posts from single file or directory
        """
        path = self.blog.backend_file
        folder, filename = os.path.split(path)

        if filename:
            content = self.get_file(path)
            posts = self.parser.unpack(content)
        else:
            posts = []
            file_list = self._list_path(path)
            for filename in file_list:
                content = self.get_file(path)
                post = self.parser.parse(content)
                posts.append(post)
        return posts

    @property
    def last_sync(self):
        return parse(self.client.metadata(self.blog.backend_file)['modified'])
