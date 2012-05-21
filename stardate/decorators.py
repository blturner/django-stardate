from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from dropbox import client, session
from dropbox.rest import ErrorResponse

from stardate.models import DropboxAuth


APP_KEY = settings.DROPBOX_APP_KEY
APP_SECRET = settings.DROPBOX_APP_SECRET
ACCESS_TYPE = settings.DROPBOX_ACCESS_TYPE


def _save_access_token(user, access_token):
    try:
        dropbox_user = user.dropbox
    except:
        dropbox_user = DropboxAuth()
        dropbox_user.user = user
    dropbox_user.access_token = access_token
    dropbox_user.save()


def _get_authorize_url(request, session):
    request_token = session.obtain_request_token()
    request.session['DROPBOX_REQUEST_TOKEN'] = request_token
    callback_url = request.build_absolute_uri()

    url = session.build_authorize_url(request_token, oauth_callback=callback_url)
    return HttpResponseRedirect(url)


def dropbox_auth(func):
    @login_required
    def wrapper(request, *args, **kwargs):
        sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
        try:
            if 'DROPBOX_REQUEST_TOKEN' in request.session:
                request_token = request.session['DROPBOX_REQUEST_TOKEN']
                access_token = sess.obtain_access_token(request_token)
                _save_access_token(request.user, access_token)
                request.session.pop('DROPBOX_REQUEST_TOKEN')
            else:
                access_token = request.user.dropbox.access_token
                secret = access_token.split('&')[0].split('=')[1]
                token = access_token.split('&')[1].split('=')[1]
                sess.set_token(token, secret)
        except:
            return _get_authorize_url(request, sess)

        try:
            c = client.DropboxClient(sess)
            return func(request, klient=c, *args, **kwargs)
        except ErrorResponse, e:
            if e.status == 401:
                _get_authorize_url(request, sess)
            else:
                raise e
    return wrapper
