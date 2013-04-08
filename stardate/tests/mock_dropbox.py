import json


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

    def __init__(self, sess=None):
        self.sess = sess

    def delta(self, cursor):
        return json.loads(self.data)

    def get_file(self, path):
        return MockFile("publish: 2012-01-02 12:00 AM\ntitle: Tingling of the spine\n\n\nExtraordinary claims require extraordinary evidence!\n\n---\n\npublish: 2012-01-01 06:00 AM\ntitle: Great turbulent clouds\n\n\nWith pretty stories for which there's little good evidence.\n")

    def metadata(self, path='/', hash=None):
        return json.loads(self.metadata_data)

    def put_file(self, full_path, file_obj, overwrite=False, parent_rev=None):
        return MockFile(file_obj)


class MockFile(object):
    def __init__(self, content):
        self.content = content

    def read(self):
        return self.content
