import os
import json

from django.core.management.base import BaseCommand

from stardate.dropbox_auth import DropboxAuth
from stardate.models import Blog, DropboxFile, Post
from stardate.parser import Stardate
from stardate.utils import prepare_bits


class Command(BaseCommand):
    args = '<blog_id blog_id ...>'
    help = 'Imports posts for the specified blogs'
    _cursor = None

    def handle(self, client=DropboxAuth(), *args, **kwargs):
        self.get_cursor()
        client = client.dropbox_client
        delta = client.delta(cursor=self._cursor)
        stardate = Stardate()

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

                    blogs = Blog.objects.filter(dropbox_file=obj)
                    for blog in blogs:
                        posts = stardate.parse(obj.content)
                        if posts:
                            for post in posts:
                                post['blog_id'] = blog.id
                                try:
                                    p = Post.objects.get(stardate=post.get("stardate"))
                                except Post.DoesNotExist:
                                    p = Post(**post)
                                p.__dict__.update(**post)
                                try:
                                    p.save()
                                except:
                                    pass

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
