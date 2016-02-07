import os

import django

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def get_env_variable(var_name):
    """ Get the environment variable or return an exception. """
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the %s environment variable" % var_name
        raise ImproperlyConfigured(error_msg)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'example.db'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

TIME_ZONE = 'UTC'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = ''

MEDIA_URL = ''

STATIC_ROOT = ''

STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# DON'T REUSE THIS SECRET KEY
SECRET_KEY = ')j40v0#o+x4_u)m*&amp;scv&amp;v55qql4xrb228au&amp;o8j%!7)ar%mhc'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates'),]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
            ]
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'example.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'example.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'core',
    'social.apps.django_app.default',
    'stardate',
)

AUTHENTICATION_BACKENDS = (
    'social.backends.dropbox.DropboxOAuth',
    'django.contrib.auth.backends.ModelBackend',
)

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

if django.VERSION[:2] < (1, 6):
    TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'

STARDATE_BACKEND = 'stardate.backends.dropbox.DropboxBackend'
STARDATE_POST_MODEL = 'stardate.Post'

try:
    DROPBOX_APP_KEY = get_env_variable('DROPBOX_APP_KEY') or 'fake_key'
    DROPBOX_APP_SECRET = get_env_variable('DROPBOX_APP_SECRET') or 'fake_secret'
except:
    DROPBOX_APP_KEY = 'fake_key'
    DROPBOX_APP_SECRET = 'fake_key'

DROPBOX_ACCESS_TYPE = 'app_folder'

# DJANGO-SOCIAL-AUTH
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/create/'
SOCIAL_AUTH_DROPBOX_KEY = DROPBOX_APP_KEY
SOCIAL_AUTH_DROPBOX_SECRET = DROPBOX_APP_SECRET
