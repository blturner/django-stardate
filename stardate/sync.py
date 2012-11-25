import copy

from dateutil.parser import parse
from django.conf import settings
from dropbox import client, session

from stardate.parser import Stardate


class StardateSync(object):
    """
    An object for interacting with the Dropbox API.

    Inspired by Michael Shepanski's django-dbbackup: https://bitbucket.org/mjs7231/django-dbbackup.
    """
    APP_KEY = settings.DROPBOX_APP_KEY
    APP_SECRET = settings.DROPBOX_APP_SECRET
    ACCESS_TYPE = settings.DROPBOX_ACCESS_TYPE

    def __init__(self, auth, client=client.DropboxClient):
        self.auth = auth
        self.client = client
        self.cursor = self.get_cursor()
        self.dropbox_client = self.get_dropbox_client()
        self.parser = Stardate()

    def get_access_token(self):
        bits = {}
        token = self.auth.extra_data['access_token']
        for bit in token.split('&'):
            b = bit.split('=')
            bits[b[0]] = b[1]
        return bits

    def get_cursor(self):
        try:
            cursor = self.auth.extra_data['cursor']
        except KeyError:
            cursor = None
        return cursor

    def get_dropbox_client(self):
        sess = session.DropboxSession(self.APP_KEY,
            self.APP_SECRET, self.ACCESS_TYPE)
        token = self.get_access_token()
        sess.set_token(token['oauth_token'], token['oauth_token_secret'])
        return self.client(sess)

    def process_dropbox_entries(self, force=False):
        from stardate.models import Blog, DropboxFile
        cursor = self.cursor
        if force:
            cursor = None
        delta = self.dropbox_client.delta(cursor=cursor)
        entries = delta.get('entries')
        if entries:
            for entry in entries:
                path = entry[0]
                metadata = self.prepare_metadata(entry[1])

                if metadata and not metadata.get('is_dir'):
                    try:
                        obj = DropboxFile.objects.get(path=path)
                        obj.__dict__.update(**metadata)
                    except DropboxFile.DoesNotExist:
                        obj = DropboxFile(**metadata)
                    obj.content = self.dropbox_client.get_file(path).read()
                    obj.save()
            self.save_cursor(delta.get('cursor'))

            for blog in Blog.objects.all():
                blog.save_stardate_posts()
        else:
            print u'No updates found.'

    def prepare_metadata(self, metadata, parent=None):
        bits = copy.copy(metadata)
        try:
            bits.pop('contents')
        except:
            pass
        try:
            bits['modified'] = parse(bits.get('modified'))
            bits['client_mtime'] = parse(bits.get('client_mtime'))
        except:
            pass
        if parent:
            bits['folder'] = parent
        return bits

    def save_cursor(self, cursor):
        self.auth.extra_data['cursor'] = cursor
        self.auth.save()
        self.cursor = self.get_cursor()
