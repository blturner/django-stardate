from __future__ import absolute_import
import os

from django.conf import settings
from django.core.cache import cache
from django.core.serializers import serialize

from stardate.backends import StardateBackend
from stardate.parsers import FileParser


class LocalFileBackend(StardateBackend):
    def __init__(self):
        self.name = u'localfile'
        self.parser = FileParser()
        self.social_auth = None

    def get_name(self):
        return self.name

    def set_social_auth(self, *args, **kwargs):
        return

    def get_posts(self, path):
        """
        Gets a list of dictionaries of posts from the backend.

        """
        content = self.get_file(path)
        return self.parser.unpack(content)

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
        if os.path.exists(blog_path):
            with open(blog_path, 'r') as f:
                content = f.read()
            remote_posts = self.parser.unpack(content)
        else:
            remote_posts = []

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
        with open(blog_path, 'w') as f:
            f.write(content)
        return

    def sync_post_files(self, blog_dir, posts):
        """
        Update posts in multiple files
        """
        for post in posts:
            # Generate the post file path dynamically
            post_path = self.get_post_path(blog_dir, post)

            # Get the existing remote post as a post dict
            if os.path.exists(post_path):
                with open(post_path, 'r') as f:
                    remote_post = f.read()
                    remote_post = self.parser.parse(remote_post)
            else:
                remote_post = {}

            # Turn local post into post dict
            local_post = self.serialize_posts([post])[0]

            # Update the contents of the remote post
            remote_post.update(local_post)
            content = self.parser.render(remote_post)
            with open(post_path, 'w') as f:
                f.write(content)
        return

    def sync(self, posts):
        """
        Render posts to local files

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
