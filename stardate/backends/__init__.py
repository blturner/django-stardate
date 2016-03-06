import os
import logging

from datetime import datetime

from django.conf import settings
from django.core.serializers import serialize
from django.utils.timezone import utc

try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module

from stardate.utils import get_post_model


Post = get_post_model()

logger = logging.getLogger('stardate')

DEFAULT_BACKENDS = {
    'local': {
        'name': 'Local',
        'module': 'stardate.backends.local_file.LocalFileBackend',
    },
    'dropbox': {
        'name': 'Dropbox',
        'module': 'stardate.backends.dropbox.DropboxBackend',
    }
}

STARDATE_BACKENDS = getattr(settings, 'STARDATE_BACKENDS', DEFAULT_BACKENDS)


def get_backend(backend=None):
    i = backend.rfind('.')
    module, attr = backend[:i], backend[i + 1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        print e
    try:
        backend_class = getattr(mod, attr)
    except AttributeError:
        print module
    return backend_class()


class StardateBackend(object):
    def __init__(self, name=None, parser=None, social_auth=None):
        self.name = name
        self.parser = parser
        self.social_auth = social_auth

    def set_social_auth(self, *args, **kwargs):
        raise NotImplementedError

    def get_name(self):
        return self.name

    def serialize_posts(self, posts):
        """
        Returns dictionary version of Post objects
        """
        posts_as_dicts = []
        serialized = serialize(
            'python',
            posts,
            fields=('title', 'slug', 'publish', 'stardate', 'body', 'timezone')
        )
        for post in serialized:
            if post['fields']['publish']:
                post['fields']['publish'] = datetime.strftime(
                    post['fields']['publish'].astimezone(utc),
                    '%Y-%m-%d %I:%M %p %Z'
                )

            posts_as_dicts.append(post['fields'])
        return posts_as_dicts

    def _update_from_dict(self, blog, post_dict, post=None):
        """
        Create or update a Post from a dictionary
        """
        created = False
        # If a post is not provided, try and fetch it
        if not post:
            if 'stardate' in post_dict:
                post = Post.objects.filter(
                    blog=blog,
                    stardate=post_dict['stardate']
                )
                if post:
                    post = post[0]
            if not post:
                post_dict['blog'] = blog
                post, created = Post.objects.get_or_create(**post_dict)

        # Update from dict values
        if not created:
            for att, value in post_dict.items():
                setattr(post, att, value)
            post.save(push=False)
        logger.info('Blog: %s, Post: %s, created=%s', post.blog, post, created)
        return post

    def push_blog_file(self, file_path, posts):
        """
        Update posts in a single blog file
        """
        remote_posts = self.get_posts(file_path)

        # Use serialized version of posts to find
        # and update
        local_posts = self.serialize_posts(posts)

        # Update remote_posts with local versions
        ## FIXME: n^2 crawl, use stardate as keys
        ## in dicts instead of lists?
        for local_post in local_posts:
            exists = False
            # First we try to see if match by stardate exists
            for remote_post in remote_posts:
                if 'stardate' in remote_post:
                    if local_post['stardate'] == remote_post['stardate']:
                        exists = True
                        remote_post.update(local_post)
                        break

            # If post was created remotely and was pulled in
            # then it has a stardate, but remote post does not.
            # Try to match up using title
            if not exists:
                for remote_post in remote_posts:
                    if 'title' in remote_post:
                        if local_post['title'] == remote_post['title']:
                            exists = True
                            remote_post.update(local_post)
                            break

            # Add new remote post if it does not exist yet
            if not exists:
                remote_posts.append(local_post)

        # Turn post list back into string
        content = self.parser.pack(remote_posts)
        self.write_file(file_path, content)
        return


    def push_post_files(self, folder, posts):
        """
        Update posts in multiple files
        """
        local_posts = self.serialized_posts(posts)

        for local_post in local_posts:
            # Generate the post file path dynamically
            post_path = self._get_post_path(folder, local_post)

            # Get the existing remote post as a post dict
            remote_post = self.get_post(post_path)

            # Update the contents of the remote post
            remote_post.update(local_post)
            content = self.parser.render(remote_post)
            self.write_file(content)
        return


    def push(self, posts):
        """
        Render posts to files

        posts: List of Post object instances
        """
        # Grab the file or folder path associated
        # with a blog
        blog_path = posts[0].blog.backend_file

        # Separate blog path into directory and filename
        blog_dir, blog_file = os.path.split(blog_path)

        # pushing works differently depending on whether
        # We are using a single file or a directory of files
        if blog_file:
            responses = [self.push_blog_file(blog_path, posts)]

        else:
            responses = self.push_post_files(blog_dir, posts)

        return responses

    def pull(self, blog):
        """
        Update local posts from remote source

        blog: Blog instance
        """
        remote_posts = self.get_posts(blog.backend_file)

        updated_list = []
        for remote_post in remote_posts:
            updated = self._update_from_dict(blog, remote_post)
            updated_list.append(updated)

        return updated_list


class BaseStardateParser(object):
    def pack(self):
        raise NotImplementedError

    def unpack(self):
        raise NotImplementedError
