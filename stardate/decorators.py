from django.contrib.auth.decorators import login_required

from stardate.dropbox_auth import DropboxAuth


def dropbox_auth_required(func):
    @login_required
    def wrapper(request, *args, **kwargs):
        c = DropboxAuth()
        return func(request, klient=c.dropbox_client, *args, **kwargs)
    return wrapper
