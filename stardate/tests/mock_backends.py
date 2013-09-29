import json
import mimetypes

from stardate.backends.dropbox import DropboxBackend
from stardate.backends.local_file import LocalFileBackend


class MockDropboxClient(object):
    entry_data = [['/test_file.md', {
        'size': '452 bytes',
        'rev': '7cb07486f6b',
        'thumb_exists': False,
        'bytes': 452,
        'modified': 'Mon, 16 Jul 2012 00:32:36 +0000',
        'mime_type': 'application/octet-stream',
        'path': '/test_file.md',
        'is_dir': False,
        'icon': 'page_white',
        'root': 'app_folder',
        'client_mtime': 'Mon, 16 Jul 2012 00:32:36 +0000',
        'revision': 1995}]]

    data = json.dumps({
        'entries': entry_data,
        'reset': False,
        'cursor': 'VAU6GZG5NK31AW2YD8H7UDWE0W74VV',
        'has_more': False
    })

    metadata_data = json.dumps({
        'bytes': 0,
        'contents': [
            {
                'bytes': 0,
                'icon': 'folder',
                'is_dir': True,
                'modified': 'Thu, 25 Aug 2011 00:03:15 +0000',
                'path': '/Sample Folder',
                'rev': '803beb471',
                'revision': 8,
                'root': 'dropbox',
                'size': '0 bytes',
                'thumb_exists': False
            },
            {
                'bytes': 77,
                'icon': 'page_white_text',
                'is_dir': False,
                'mime_type': 'text/plain',
                'modified': 'Wed, 20 Jul 2011 22:04:50 +0000',
                'path': '/magnum-opus.txt',
                'rev': '362e2029684fe',
                'revision': 221922,
                'root': 'dropbox',
                'size': '77 bytes',
                'thumb_exists': False
            }
        ],
        'hash': 'efdac89c4da886a9cece1927e6c22977',
        'icon': 'folder',
        'is_dir': True,
        'path': '/',
        'root': 'app_folder',
        'size': '0 bytes',
        'thumb_exists': False
    })

    metadata_data_2 = json.dumps({
        'bytes': 0,
        'contents': [
            {
                'bytes': 77,
                'icon': 'page_white_text',
                'is_dir': False,
                'mime_type': 'text/plain',
                'modified': 'Wed, 20 Jul 2011 22:04:50 +0000',
                'path': '/Sample Folder/magnum-opus.txt',
                'rev': '362e2029684fe',
                'revision': 221922,
                'root': 'dropbox',
                'size': '77 bytes',
                'thumb_exists': False
            }
        ],
        'hash': 'efdac89c4da886a9cece1927e6c22977',
        'icon': 'folder',
        'is_dir': True,
        'path': '/Sample Folder',
        'root': 'app_folder',
        'size': '0 bytes',
        'thumb_exists': False
    })

    def __init__(self, sess=None):
        self.sess = sess

    def delta(self, cursor):
        return json.loads(self.data)

    def get_file(self, path):
        f = open(path, 'r')
        return f

    def metadata(self, path='/', hash=None):
        data = {}
        if path == '/Sample Folder':
            data = json.loads(self.metadata_data_2)
        if path == '/':
            data = json.loads(self.metadata_data)
        return data

    def put_file(self, full_path, file_obj, overwrite=False, parent_rev=None):
        f = open(full_path, 'w')
        f.write(file_obj)
        f.close()
        resp = {
            'path': full_path,
            'mime_type': mimetypes.guess_type(full_path),
        }
        return resp


class MockDropboxBackend(DropboxBackend):
    def __init__(self, client_class=MockDropboxClient):
        return super(MockDropboxBackend, self).__init__(client_class=client_class)


class MockLocalFileBackend(LocalFileBackend):
    pass
