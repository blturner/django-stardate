import copy
from datetime import datetime, timedelta

from django.conf import settings
from django.shortcuts import render_to_response
from dropbox.rest import ErrorResponse

from stardate.decorators import dropbox_auth_required
from stardate.models import DropboxFile, DropboxFolder, Blog, Post


APP_KEY = settings.DROPBOX_APP_KEY
APP_SECRET = settings.DROPBOX_APP_SECRET
ACCESS_TYPE = settings.DROPBOX_ACCESS_TYPE
timeformat = "%a, %d %b %Y %H:%M:%S"


def format_timestamp(string, format):
    timestamp = string[:-6]
    offset = int(string[-5:])
    delta = timedelta(hours=offset / 100)
    d = datetime.strptime(timestamp, format)
    d -= delta
    return d


def _prepare_bits(metadata, parent):
    bits = copy.copy(metadata)
    try:
        bits.pop('contents')
    except:
        pass
    try:
        bits['modified'] = format_timestamp(bits.get('modified'), timeformat)
        bits['client_mtime'] = format_timestamp(bits.get('client_mtime'), timeformat)
    except:
        pass
    if parent:
        bits['folder'] = parent
    return bits


def _save_file_or_folder(klient, path, parent=None):
    f = None
    hash = None

    if DropboxFolder.objects.filter(path=path).exists():
        f = DropboxFolder.objects.get(path=path)
        hash = f.hash
    elif DropboxFile.objects.filter(path=path).exists():
        f = DropboxFile.objects.get(path=path)
    else:
        pass

    try:
        metadata = klient.metadata(path, hash=hash)
        if metadata['is_dir']:
            bits = _prepare_bits(metadata, parent)
            if f:
                f.__dict__.update(**bits)
            else:
                f = DropboxFolder(**bits)
            f.save()
            for content in metadata['contents']:
                _save_file_or_folder(klient, content['path'], parent=f)
        else:
            bits = _prepare_bits(metadata, parent)
            if f:
                f.__dict__.update(**bits)
            else:
                f = DropboxFile(**bits)
            f.save()
        return metadata
    except ErrorResponse, e:
        if e.status == 304:
            return e.status
        else:
            raise e


@dropbox_auth_required
def read_dir(request, klient, path='/'):
    metadata = _save_file_or_folder(klient, path)
    return render_to_response('metadata.html', {'metadata': metadata})


@dropbox_auth_required
def import_posts(request, klient):
    blogs = Blog.objects.all()

    for blog in blogs:
        dfile = blog.dropbox_file
        content = klient.get_file(dfile.path)
        p = Post()
        p.content = content.read()
        p.blog = blog
        p.save()
        content.close()
    return render_to_response('metadata.html', {'metadata': p.content})
