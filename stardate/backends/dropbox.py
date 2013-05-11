from __future__ import absolute_import
import os

from django.conf import settings
from django.core.cache import cache
from django.core.serializers import serialize

from dropbox import client, rest, session

from stardate.backends import StardateBackend
from stardate.parsers import FileParser


APP_KEY = getattr(settings, 'DROPBOX_APP_KEY', None)
APP_SECRET = getattr(settings, 'DROPBOX_APP_SECRET', None)
ACCESS_TYPE = getattr(settings, 'DROPBOX_ACCESS_TYPE', None)


class DropboxBackend(StardateBackend):
    def __init__(self, client_class=client.DropboxClient):
        self.client = None
        self.client_class = client_class
        self.cursor = self.get_cursor()
        self.name = u'dropbox'
        self.parser = FileParser()
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
        sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
        token = self.get_access_token()
        sess.set_token(token['oauth_token'], token['oauth_token_secret'])
        return self.client_class(sess)

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

    def save_cursor(self, cursor):
        self.social_auth.extra_data['cursor'] = cursor
        self.social_auth.save()
        self.cursor = self.get_cursor()

    def set_social_auth(self, social_auth):
        self.social_auth = social_auth
        self.client = self.get_dropbox_client()

    def serialize_posts(self, posts):
        """
        Returns dictionary of individual Post
        """
        posts_as_dicts = []
        serialized = serialize(
            'python',
            posts,
            fields=('title', 'publish', 'stardate', 'body')
        )
        for post in serialized:
            posts_as_dicts.append(post['fields'])
        return posts_as_dicts

    def get_post_path(self, folder, post):
        """
        Dynamically guess post file path from slug / blog folder
        """
        filename = post.slug
        filename = '{0}.md'.format(filename)
        path = os.path.join(folder, filename)
        return path

    def sync_blog_file(self, blog_path, posts):
        """
        Update posts in a single blog file
        """
        content = self.client.get_file(blog_path).read()
        remote_posts = self.parser.unpack(content)

        # Use serialized version of posts to find
        # and update
        local_posts = self.serialize_posts(posts)

        # Update remote_posts with local versions
        ## FIXME: n^2 crawl, use stardate as keys
        ## in dicts instead of lists?
        for local_post in local_posts:
            exists = False
            for remote_post in remote_posts:
                if local_post['stardate'] == remote_post['stardate']:
                    exists = True
                    remote_post.update(local_post)
            # Add new remote post if it does not exist yet
            if not exists:
                remote_posts.append(local_post)

        # Turn post list back into string
        content = self.parser.pack(remote_posts)
        return self.client.put_file(blog_path, content, overwrite=True)

    def sync_post_files(self, blog_dir, posts):
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

            print local_post['body']

            # Update the contents of the remote post
            remote_post.update(local_post)
            content = self.parser.render(remote_post)
            print content
            response = self.client.put_file(post_path, content, overwrite=True)

            # Log the result
            responses.append(response)
        return responses

    def push(self, posts):
        """
        Sync one or more posts with remote Dropbox

        posts: List of Post object instances
        """
        # Grab the file or folder path associated
        # with a blog
        blog_path = posts[0].blog.backend_file

        # Separate blog path into directory and filename
        blog_dir, blog_file = os.path.split(blog_path)

        # Syncing works differently depending on whether
        # We are using a single file or a directory of files
        if blog_file:
            responses = [self.sync_blog_file(blog_path, posts)]

        else:
            responses = self.sync_post_files(blog_dir, posts)

        return responses
