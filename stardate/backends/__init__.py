import os
import logging

from datetime import datetime

from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.timezone import utc

try:
    from django.db.transaction import atomic
except ImportError:
    from django.db.transaction import commit_on_success as atomic

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


def get_backend(backend=None, blog=None):
    i = backend.rfind('.')
    module, attr = backend[:i], backend[i + 1:]
    try:
        mod = import_module(module)
    except ImportError as err:
        logger.error(err)
    try:
        backend_class = getattr(mod, attr)
    except AttributeError:
        print (module)
    return backend_class(blog=blog)


class StardateBackend(object):
    def __init__(self, *args, **kwargs):
        self.blog = kwargs.get('blog', None)
        self.name = kwargs.get('name', None)
        self.parser = kwargs.get('parser', None)
        self.social_auth = kwargs.get('social_auth', None)

    def get_name(self):
        return self.name

    def _get_post_path(self, folder, post):
        """
        Dynamically guess post file path from slug / blog folder
        """
        filename = slugify(post['title'])
        filename = '{0}.md'.format(filename)
        path = os.path.join(folder, filename)
        return path

    def _update_from_dict(self, blog, post_dict, post=None):
        """
        Create or update a Post from a dictionary
        """
        created = False
        # If a post is not provided, try and fetch it
        if not post:
            if 'stardate' in post_dict:
                post = Post.objects.get(
                    blog=blog,
                    stardate=post_dict['stardate']
                )
            if not post:
                post_dict['blog'] = blog
                post, created = Post.objects.get_or_create(**post_dict)

        push = False

        for key, value in post_dict.items():
            post_value = getattr(post, key)

            if key == 'body':
                post_value = getattr(post, key).raw

            if value != post_value:
                push = True

        # Update from dict values
        if not created:
            for att, value in post_dict.items():
                setattr(post, att, value)
            logger.debug('push is {}'.format(push))
            post.save(push=push)
        logger.info('Blog: %s, Post: %s, created=%s', post.blog, post, created)
        return post

    def get_posts(self):
        """
        Fetch post dictionaries from single file or directory by reading and
        parsing file content into post dictionaries.

        Returns an array of Post dictionairies.
        """
        path = self.blog.backend_file
        ext = get_extension(path)
        posts = []

        if ext:
            content = self.get_file(path)
            if content:
                posts = self.parser.unpack(content)
        else:
            for file_name in self._list_path(path):
                content = self.get_file(file_name)

                try:
                    post = self.parser.parse(content)
                    posts.append(post)
                except:
                    continue
        return posts

    def push_blog_file(self, posts):
        """
        Update posts in a single blog file
        """
        remote_posts = self.get_posts()

        # Use serialized version of posts to find
        # and update
        local_posts = [post.serialized() for post in posts]

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

        return self.write_file(self.blog.backend_file, content)

    def write_file(self, path, content):
        raise NotImplementedError

    def push_post_files(self, folder, posts):
        """
        Update posts in multiple files
        """
        local_posts = [post.serialized() for post in posts]

        for local_post in local_posts:
            # Generate the post file path dynamically
            post_path = self._get_post_path(folder, local_post)

            # Get the existing remote post as a post dict
            remote_post = self.get_post(post_path)

            # Update the contents of the remote post
            remote_post.update(local_post)
            content = self.parser.render(remote_post)
            self.write_file(post_path, content)
        return


    def push(self, posts):
        """
        Render posts to files

        posts: List of Post object instances
        """
        if not self.blog.sync:
            return []

        # Grab the file or folder path associated
        # with a blog
        blog_path = append_slash(self.blog.backend_file)

        # Separate blog path into directory and filename
        blog_dir, blog_file = os.path.split(blog_path)

        # pushing works differently depending on whether
        # We are using a single file or a directory of files
        if blog_file:
            responses = [self.push_blog_file(posts)]

        else:
            responses = self.push_post_files(blog_dir, posts)

        return responses

    def pull(self, force=False):
        """
        Update local posts from remote source

        blog: Blog instance
        """
        blog = self.blog
        last_sync = blog.backend.last_sync
        updated_list = []

        if not blog.sync:
            return updated_list

        if not force:
            if blog.last_sync and not blog.last_sync < last_sync:
                logger.info(u'Nothing to update. Last sync was {}'.format(datetime.strftime(last_sync, '%c')))
                return updated_list
        else:
            logger.info(u'Forced sync using --force')

        remote_posts = self.get_posts()

        for remote_post in remote_posts:
            updated = self._update_from_dict(blog, remote_post)
            updated_list.append(updated)

        batch_save(updated_list)
        logger.info(u'Updated {} posts for {}'.format(len(updated_list), blog))

        blog.last_sync = blog.backend.last_sync
        blog.save()
        logger.info('last_sync updated: {}'.format(last_sync))

        return updated_list


def append_slash(path):
    ext = get_extension(path)
    if not ext and path[-1] != '/':
        path = path + '/'
    return path


def get_extension(path):
    return os.path.splitext(path)[-1].lower()


@atomic
def batch_save(queryset):
    for obj in queryset:
        push = False

        if obj.stardate:
            push = True

        obj.save(push=push)


class BaseStardateParser(object):
    def pack(self):
        raise NotImplementedError

    def unpack(self):
        raise NotImplementedError
