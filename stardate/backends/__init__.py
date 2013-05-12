from django.conf import settings
from django.utils.importlib import import_module


STARDATE_BACKEND = getattr(settings, 'STARDATE_BACKEND', 'stardate.backends.dropbox.DropboxBackend')


def get_backend(backend=STARDATE_BACKEND):
    i = backend.rfind('.')
    module, attr = backend[:i], backend[i + 1:]
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
    pass


class BaseStardateParser(object):
    def pack(self):
        raise NotImplementedError

    def unpack(self):
        raise NotImplementedError
