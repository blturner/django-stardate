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

    def __init__(self, sess=None):
        self.sess = sess

    def delta(self, cursor):
        return json.loads(self.data)

    def get_file(self, path):
        return MockFile("publish: 2012-01-02 12:00 AM\ntitle: Tingling of the spine\n\n\nExtraordinary claims require extraordinary evidence!\n\n---\n\npublish: 2012-01-01 06:00 AM\ntitle: Great turbulent clouds\n\n\nWith pretty stories for which there's little good evidence.\n")

    def put_file(self, full_path, file_obj, overwrite=False, parent_rev=None):
        return MockFile(file_obj)


class MockFile(object):
    def __init__(self, content):
        self.content = content

    def read(self):
        return self.content
