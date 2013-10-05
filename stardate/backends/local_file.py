from __future__ import absolute_import
import os



from stardate.backends import StardateBackend
from stardate.parsers import FileParser


class LocalFileBackend(StardateBackend):
    def __init__(self):
        self.name = u'localfile'
        self.parser = FileParser()
        self.social_auth = None

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
            post = self.parser.parser(post)
        else:
            post = {}
        return post

    def get_posts(self, path):
        """
        Fetch post dictionaries from single file or directory
        """
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

    def set_social_auth(self, *args, **kwargs):
        return

    def _get_post_path(self, folder, post):
        """
        Dynamically guess post file path from slug / blog folder
        """
        filename = post['slug']
        filename = '{0}.md'.format(filename)
        path = os.path.join(folder, filename)
        return path
