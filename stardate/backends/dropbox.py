from __future__ import absolute_import
import json
import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import make_aware, is_aware

from dropbox import Dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode

from stardate.backends import StardateBackend
from stardate.parsers import FileParser


logger = logging.getLogger('stardate')


class DropboxBackend(StardateBackend):
    def __init__(self, *args, **kwargs):
        super(DropboxBackend, self).__init__(*args, **kwargs)
        self.client = self.get_dropbox_client()
        self.name = u'dropbox'
        self.parser = FileParser()

    def get_file(self, path):
        metadata, file = self.client.files_download(path)

        return file.content

    def write_file(self, file_path, content):
        return self.client.files_upload(content.encode('utf-8'), file_path, mode=WriteMode('overwrite', None))

    def get_social_auth(self):
        return self.blog.user.social_auth.get(provider='dropbox-oauth2')

    def get_post(self, path):
        try:
            content = self.get_file(path)
            post = self.parser.parse(content)
        except Exception:
            post = {}
        return post

    def get_access_token(self):
        extra_data = self.get_social_auth().extra_data
        try:
            if isinstance(extra_data, unicode):
                extra_data = json.loads(extra_data)
        except NameError:
            pass
        return extra_data.get('access_token')

    def get_cursor(self):
        extra_data = self.get_social_auth().extra_data
        try:
            if isinstance(extra_data, unicode):
                extra_data = json.loads(extra_data)
        except NameError:
            pass
        return extra_data.get('cursor')

    def get_dropbox_client(self):
        token = self.get_access_token()
        return Dropbox(token)

    def _list_path(self, path='/', hash=None):
        """
        List the contents of a path on the backend. Each path can be passed
        a `hash` argument that determines if anything new for the specified
        path is returned.

        """
        paths = cache.get('paths', [])
        meta_hash = cache.get('hash', None)

        try:
            meta = self.client.files_get_metadata(path)
            cache.delete('paths')
            cache.set('hash', meta['hash'])
        except ApiError as err:
            raise err

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
        social_auth = self.get_social_auth()
        extra_data = social_auth.extra_data
        try:
            if isinstance(extra_data, unicode):
                extra_data = json.loads(extra_data)
        except NameError:
            pass
        extra_data['cursor'] = cursor
        social_auth.extra_data = extra_data
        social_auth.save()

    @property
    def last_sync(self):
        modified = self.client.files_get_metadata(
            self.blog.backend_file
        ).server_modified

        if not is_aware(modified):
            modified = make_aware(modified)

        return modified
