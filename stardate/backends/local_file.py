from __future__ import absolute_import
import os

from django.core.serializers import serialize

from stardate.backends import StardateBackend
from stardate.parsers import FileParser
from stardate.models import Post


class LocalFileBackend(StardateBackend):
    def __init__(self):
        self.name = u'localfile'
        self.parser = FileParser()
        self.social_auth = None

    def get_name(self):
        return self.name

    def set_social_auth(self, *args, **kwargs):
        return

    def serialize_posts(self, posts):
        """
        Returns dictionary of individual Post
        """
        posts_as_dicts = []
        serialized = serialize(
            'python',
            posts,
            fields=('title', 'slug', 'created', 'publish', 'stardate', 'body')
        )
        for post in serialized:
            posts_as_dicts.append(post['fields'])
        return posts_as_dicts

    def _get_post_path(self, folder, post):
        """
        Dynamically guess post file path from slug / blog folder
        """
        filename = post['slug']
        filename = '{0}.md'.format(filename)
        path = os.path.join(folder, filename)
        return path

    def _posts_from_file(self, file_path):
        """
        Return list of post dictionaries from file
        """
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            posts = self.parser.unpack(content)
        else:
            posts = []
        return posts

    def _posts_from_dir(self, folder, posts=[]):
        """
        Get posts dicts from files in a directory
        """
        files = os.listdir(folder)
        remote_posts = []
        for filename in files:
            with open(os.path.join(folder, filename), 'r') as f:
                remote_post = f.read()
            remote_post = self.parser.parse(remote_post)
            remote_posts.append(remote_post)

        return remote_posts

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
            responses = [self._push_blog_file(blog_path, posts)]

        else:
            responses = self._push_post_files(blog_dir, posts)

        return responses

    def _push_blog_file(self, file_path, posts):
        """
        Update posts in a single blog file
        """
        remote_posts = self._posts_from_file(file_path)

        # Use serialized version of posts to find
        # and update
        local_posts = self.serialize_posts(posts)

        # Update remote_posts with local versions
        ## FIXME: n^2 crawl, use stardate as keys
        ## in dicts instead of lists?
        for local_post in local_posts:
            exists = False
            for remote_post in remote_posts:
                if 'stardate' in remote_post:
                    if local_post['stardate'] == remote_post['stardate']:
                        exists = True
                        remote_post.update(local_post)
                # Post may exist on backend with uuid, but
                # also exist in local from last pull where
                # uuid was assigned. Use 'title' field as
                # backup
                else:
                    try:
                        if local_post['title'] == remote_post['title']:
                            exists = True
                            remote_post.update(local_post)
                    except KeyError:
                        pass
            # Add new remote post if it does not exist yet
            if not exists:
                remote_posts.append(local_post)

        # Turn post list back into string
        content = self.parser.pack(remote_posts)
        with open(file_path, 'w') as f:
            f.write(content)
        return

    def _push_post_files(self, folder, posts):
        """
        Update posts in multiple files
        """
        local_posts = self.serialized_posts(posts)

        for local_post in local_posts:
            # Generate the post file path dynamically
            post_path = self._get_post_path(folder, local_post)

            # Get the existing remote post as a post dict
            if os.path.exists(post_path):
                with open(post_path, 'r') as f:
                    remote_post = f.read()
                    remote_post = self.parser.parse(remote_post)
            else:
                remote_post = {}

            # Update the contents of the remote post
            remote_post.update(local_post)
            content = self.parser.render(remote_post)
            with open(post_path, 'w') as f:
                f.write(content)
        return

    def _update_from_dict(self, blog, post_dict, post=None):
        """
        Create or update a Post from a dictionary
        """
        # If a post is not provided, try an fetch it
        if not post:
            if 'stardate' in post_dict:
                post = Post.objects.filter(
                    blog=blog,
                    stardate=post_dict['stardate']
                )
                if post:
                    post = post[0]
            if not post:
                post = Post(blog=blog)

        # Update from dict values
        for att, value in post_dict.items():
            setattr(post, att, value)
        post.save(push=False)
        return post

    def pull(self, blog):
        """
        Update local posts from remote source

        blog: Blog instance
        """
        blog_path = blog.backend_file
        blog_dir, blog_file = os.path.split(blog_path)

        # Extract remote posts from single file
        if blog_file:
            remote_posts = self._posts_from_file(blog_path)
        # Extract posts from multiple files
        else:
            remote_posts = self._posts_from_dir(blog_dir)

        updated_list = []
        for remote_post in remote_posts:
            updated = self._update_from_dict(blog, remote_post)
            updated_list.append(updated)

        return updated_list
