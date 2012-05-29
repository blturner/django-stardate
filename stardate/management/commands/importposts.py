import os
import json

from django.core.management.base import BaseCommand, CommandError

from stardate.dropbox_auth import DropboxAuth
from stardate.models import DropboxFile
from stardate.utils import prepare_bits


class Command(BaseCommand):
    args = '<blog_id blog_id ...>'
    help = 'Imports posts for the specified blogs'
    _cursor = None

    def handle(self, *args, **kwargs):
        self.get_cursor()
        client = DropboxAuth().dropbox_client
        delta = client.delta(cursor=self._cursor)

        if delta.get('entries'):
            for entry in delta.get('entries'):
                path = entry[0]
                metadata = entry[1]
                metadata = prepare_bits(metadata)

                if not metadata.get('is_dir'):
                    try:
                        obj = DropboxFile.objects.get(path=path)
                        obj.__dict__.update(**metadata)
                    except DropboxFile.DoesNotExist:
                        obj = DropboxFile(**metadata)
                    obj.content = client.get_file(path).read()
                    obj.save()
            self.save_cursor(delta.get('cursor'))

    def save_cursor(self, cursor):
        cursordata = dict(cursor=cursor)
        with open('data.json', 'wb') as cursorhandle:
            json.dump(cursordata, cursorhandle)

    def get_cursor(self):
        if os.path.exists('data.json'):
            with open('data.json', 'rb') as cursorhandle:
                cursordata = json.load(cursorhandle)
            self._cursor = cursordata.get('cursor')
