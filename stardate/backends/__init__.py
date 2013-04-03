from django.conf import settings
from django.utils.importlib import import_module


# STARDATE_ADAPTER = getattr(settings, 'STARDATE_ADAPTER', 'stardate.backends.dropbox.DropboxAdapter')
STARDATE_BACKEND = getattr(settings, 'STARDATE_BACKEND', 'stardate.backends.dropbox.DropboxBackend')

# def get_adapter():
#     pkg, klass = STARDATE_ADAPTER.rsplit('.', 1)
#     module = import_module(pkg)
#     return getattr(module, klass)


def get_backend():
    i = STARDATE_BACKEND.rfind('.')
    module, attr = STARDATE_BACKEND[:i], STARDATE_BACKEND[i + 1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        print e
    try:
        backend_class = getattr(mod, attr)
    except AttributeError:
        print module
    return backend_class()


class StardateBackend(object):
    # def __init__(self, adapter):
        # self.adapter = get_adapter()

    def get_client(self):
        return self.adapter.get_client()


class StardateAdapter(object):
    def __init__(self):
        self.backend = get_backend()

    def get_client(self):
        return self.backend.get_client()


class BaseStardateParser(object):
    def pack(self):
        raise NotImplementedError

    def unpack(self):
        raise NotImplementedError
