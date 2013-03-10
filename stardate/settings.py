from django.conf import settings

PROJECT_ROOT = getattr(settings, 'PROJECT_ROOT', None)

DROPBOX_APP_KEY = getattr(settings, 'DROPBOX_APP_KEY', None)
DROPBOX_APP_SECRET = getattr(settings, 'DROPBOX_APP_SECRET', None)
DROPBOX_ACCESS_TYPE = 'app_folder'
