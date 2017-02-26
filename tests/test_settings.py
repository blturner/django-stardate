import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'not_used.db',
        'TEST': {
            # Setting name forces the use of a file instead of memory
            # to prevent errors from using threads.
            'NAME': 'stardate.db',
        }
    }
}

SECRET_KEY = 'fake_key'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'social.apps.django_app.default',
    'stardate',
    'tests',
]

TIME_ZONE = 'UTC'

USE_TZ = True

# AUTHENTICATION_BACKENDS = [
#     'django.contrib.auth.backends.ModelBackend',
# ]

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

ROOT_URLCONF = 'tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, 'templates'),],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        }
    },
]

STARDATE_POST_MODEL = 'stardate.Post'

DROPBOX_APP_KEY = 'fake_key'
DROPBOX_APP_SECRET = 'fake_secret'
DROPBOX_ACCESS_TYPE = 'app_folder'

# DJANGO-SOCIAL-AUTH
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/create/'
SOCIAL_AUTH_DROPBOX_KEY = DROPBOX_APP_KEY
SOCIAL_AUTH_DROPBOX_SECRET = DROPBOX_APP_SECRET
