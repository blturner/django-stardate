from __future__ import absolute_import

import os
import time

from django.utils.timezone import make_aware, utc

from dateutil.parser import parse

from stardate.backends import StardateBackend
from stardate.parsers import FileParser


class LocalFileBackend(StardateBackend):
    def __init__(self, *args, **kwargs):
        super(LocalFileBackend, self).__init__(*args, **kwargs)
        self.name = u'localfile'
        self.parser = FileParser()

    def write_file(self, file_path, content):
        with open(file_path, 'w') as f:
            f.write(content)

    def get_file(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
        else:
            content = None
        return content

    def get_post(self, path):
        if os.path.exists(path):
            content = self.get_file(path)
            post = self.parser.parser(content)
        else:
            post = {}
        return post

    def get_posts(self):
        """
        Fetch post dictionaries from single file or directory
        """
        path = self.blog.backend_file
        # First try to parse it as a directory
        # If we fail, parse it as a file
        if os.path.isfile(path):
            content = self.get_file(path)
            posts = self.parser.unpack(content)
        elif os.path.isdir(path):
            posts = []
            file_list = self._list_path(path)
            for filename in file_list:
                file_path = os.path.join(path, filename)
                content = self.get_file(file_path)
                post = self.parser.parse(content)
                posts.append(post)
        else:
            raise Exception('File does not exist')
        return posts

    def _list_path(self, path):
        return os.listdir(path)

    @property
    def last_sync(self):
        modified = time.ctime(os.path.getmtime(self.blog.backend_file))
        return make_aware(parse(modified), utc)
