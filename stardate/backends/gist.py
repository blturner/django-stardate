from __future__ import absolute_import
import logging
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from stardate.backends import StardateBackend
from stardate.parsers import FileParser

from github import Github, InputFileContent

logger = logging.getLogger('stardate')

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

GITHUB_APP_ID = get_settings_or_env('GITHUB_APP_ID')
GITHUB_API_SECRET = get_settings_or_env('GITHUB_API_SECRET')


class GistBackend(StardateBackend):
    def __init__(self, client_class=Github):
        self.client_class = client_class
        self.client = None
        self.name = u'gist'
        self.parser = FileParser()
        self.social_auth = None


    def directory_or_file(self, backend_file):
        ## TODO: Look into editin GistFiles separately      
        return 'file'

    def write_file(self, gist_id, posts):
        """
        Update the Gist Files with content of remote_posts
        """
        gist_files = {}
        for post in posts:
            post_as_string = self.parser.render(post)
            gist_files[post['backend_file']] = InputFileContent(post_as_string)
        gist = self.client.get_gist(gist_id)
        gist.edit('Edited by Stardate', gist_files)
        return

    def get_posts(self, gist_id):
        """
        Retrieve post dictionaries from a gist id
        """
        gist = self.client.get_gist(gist_id)
        gist_files = gist.files.values()
        posts = []
        for gist_file in gist_files:
            post = self.parser.parse(gist_file.content)
            post['backend_file'] = gist_file.filename
            posts.append(post)
        return posts

    ## Social Auth Utilities
    def get_github_client(self):
        token = self.social_auth.extra_data['access_token']
        client = self.client_class(
            login_or_token=token,
            client_id=GITHUB_APP_ID,
            client_secret=GITHUB_API_SECRET
        )
        return client

    def set_social_auth(self, social_auth):
        self.social_auth = social_auth
        self.client = self.get_github_client()




